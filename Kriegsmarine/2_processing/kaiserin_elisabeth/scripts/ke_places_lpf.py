"""Historic-name gazetteer for the Kaiserin Elisabeth itinerary, as Linked Places (LPF).

    uv run python -m scripts.ke_places_lpf [--no-wikidata]

Input: prototype/data/ke_itinerary.csv (geocoded stops, GeoNames ids).
Adds per place: vault attestations (name as written in the vault, cited, with the
voyage years as ATTESTATION), GeoNames alternate names (isHistoric flag, from/to as
VALIDITY), Wikidata official names (P1448 with P580/P582) and labels.
Output: prototype/data/ke_places.lpf.json (validated against WHG's LPF v1.2.2 schema,
reference/lpf/schema_lpf_v1.2.2.json) and a coverage summary.
Upload the file to World Historical Gazetteer (browser) to reconcile against its index.
"""

from __future__ import annotations

import collections
import csv
import functools
import json
import re
import sys
from pathlib import Path

import requests

from kp import geo, places

DATA = Path("../../3_visualization/web/data")  # the web pages (Kriegsmarine/3_visualization/web)
SCHEMA = Path("reference/lpf/schema_lpf_v1.2.2.json")
SCHEMA_GET = (
    "gh api repos/WorldHistoricalGazetteer/whg3/contents/datasets/static/validate/"
    "schema_lpf_v1.2.2.json -H 'Accept: application/vnd.github.raw' > " + SCHEMA.as_posix()
)
CACHE = Path("data/geonames/alternatenames")
VAULT_CITE = "Team vault Archive_Indien_Schiffreisen (khm-team), note: "


def add_name(names, seen, toponym, lang, cite_label, cite_id, when, kind) -> None:
    """Append one LPF name with its citation; the kind (attested / historic / dated /
    current / official / label) is kept in the citation label."""
    key = (toponym, lang, kind)
    if not toponym or key in seen:
        return
    seen.add(key)
    n = {"toponym": toponym, "lang": lang, "citations": [{"label": f"{cite_label} [{kind}]"}]}
    if cite_id:
        n["citations"][0]["@id"] = cite_id
    if when:
        n["when"] = when
    names.append(n)


def main(argv: list[str]) -> int:
    rows = [
        r
        for r in csv.DictReader((DATA / "ke_itinerary.csv").open(encoding="utf-8"))
        if r["geo_status"] == "matched"
    ]
    by_place: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_place[r["place_note"]].append(r)
    gid = {p: rs[0]["geonames"].rstrip("/").rsplit("/", 1)[-1] for p, rs in by_place.items()}
    countries = {rs[0]["country"] for rs in by_place.values() if rs[0]["country"]}

    alt = places.geonames_alt_names(set(gid.values()), countries, CACHE)
    wd = {}
    if "--no-wikidata" not in argv:
        try:
            expect = {gid[p]: rs[0]["geo_name"] for p, rs in by_place.items()}
            wd = places.wikidata_by_geonames(sorted(set(gid.values())), expect)
        except (requests.RequestException, KeyError, ValueError) as e:
            # one attempt only; the file is still valid without Wikidata
            print(f"Wikidata skipped: {type(e).__name__}: {str(e)[:120]}")

    feats = []
    for place, rs in by_place.items():
        g, r0 = gid[place], rs[0]
        names: list[dict] = []
        add = functools.partial(add_name, names, set())

        # 1 vault attestations, dated by the voyage (attestation, not validity). Only the
        # period name counts: "Bombay (… Heut. Mumbai)" attests Bombay, not Mumbai.
        ys = [int(y) for r in rs for y in re.findall(r"1[89]\d\d", r["years"])]
        att = places.timespan(min(ys), max(ys)) if ys else None
        period = [h for h in r0["historic_names"].split("; ") if h]
        for t in period or [r0["geo_matched"]]:
            add(t, None, VAULT_CITE + place, None, att, "attested")
        # 2 GeoNames alternate names: historic flag and from/to (validity)
        for a in alt.get(g, []):
            if a["historic"] or a["start"] or a["end"]:
                add(
                    a["toponym"],
                    a["lang"],
                    "GeoNames alternate name",
                    f"https://www.geonames.org/{g}/",
                    # "from" without "to": still valid, unless GeoNames flags it historic
                    places.timespan(a["start"], a["end"], ongoing=not a["historic"]),
                    "historic" if a["historic"] else "dated",
                )
        add(r0["geo_name"], None, "GeoNames", f"https://www.geonames.org/{g}/", None, "current")
        # 3 Wikidata official names with validity, and labels
        w = wd.get(g)
        links = [{"type": "closeMatch", "identifier": f"https://www.geonames.org/{g}/"}]
        if w:
            links.append(
                {"type": "closeMatch", "identifier": f"http://www.wikidata.org/entity/{w['qid']}"}
            )
            for o in w["official"]:
                add(
                    o["toponym"],
                    o["lang"],
                    "Wikidata P1448",
                    f"http://www.wikidata.org/entity/{w['qid']}",
                    places.timespan(o["start"], o["end"], ongoing=True),  # P580 without P582
                    "official",
                )
            add(
                w["label_de"],
                "de",
                "Wikidata label",
                f"http://www.wikidata.org/entity/{w['qid']}",
                None,
                "label",
            )
            add(
                w["label_en"],
                "en",
                "Wikidata label",
                f"http://www.wikidata.org/entity/{w['qid']}",
                None,
                "label",
            )
        feats.append(
            {
                "@id": "ke:place/" + re.sub(r"[^a-z0-9]+", "-", geo.norm(place)).strip("-"),
                "type": "Feature",
                "properties": {
                    "title": place,
                    "ccodes": [r0["country"]] if r0["country"] else [],
                    "segments": sorted({r["segment"] for r in rs}),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(r0["longitude"]), float(r0["latitude"])],
                },
                "names": names,
                "links": links,
                "when": att or {"timespans": [{"start": {"in": ""}}]},
            }
        )

    fc = {"type": "FeatureCollection", "@context": places.LPF_CONTEXT, "features": feats}
    (DATA / "ke_places.lpf.json").write_text(
        json.dumps(fc, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    if SCHEMA.exists():
        import jsonschema  # dev dependency

        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        errors = [
            (f["@id"], e.message)
            for f in feats
            for e in jsonschema.Draft7Validator(schema).iter_errors(f)
        ]
    else:
        errors = []
        print(f"schema not found ({SCHEMA}), validation skipped. Get it with:\n  {SCHEMA_GET}")
    kinds = collections.Counter(
        n["citations"][0]["label"].rsplit("[", 1)[-1].rstrip("]") for f in feats for n in f["names"]
    )
    with_hist = sum(
        any("[historic]" in n["citations"][0]["label"] for n in f["names"]) for f in feats
    )
    with_valid = sum(
        any(n.get("when") and "[attested]" not in n["citations"][0]["label"] for n in f["names"])
        for f in feats
    )
    print(
        f"{len(feats)} places; GeoNames isHistoric name for {with_hist}; any dated validity for {with_valid}; "
        f"Wikidata item for {sum(1 for g in gid.values() if g in wd)}"
    )
    print("names by kind:", dict(kinds))
    print(f"schema errors: {len(errors)}", errors[:3])
    print(f"-> {DATA}/ke_places.lpf.json")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
