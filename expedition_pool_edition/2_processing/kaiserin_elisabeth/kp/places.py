"""Historic place names in Linked Places Format (LPF v1.2.2, World Historical Gazetteer).

Model (LPF): one Feature per place; `names[]` = toponyms, each with `lang`, `citations[]`
and an optional `when`; `links[]` = closeMatch to GeoNames / Wikidata / GND.

Two kinds of `when` are kept apart:
  attestation  a source used this name at that time (the vault: "Batavia" on the 1892-93
               voyage). Says nothing about when the name was valid.
  validity     an external source states the period (GeoNames alternate-name from/to,
               Wikidata P1448 with P580/P582). Only these are used as validity.
Every name carries its citation, so the two never mix.

Sources: GeoNames alternate names per country (offline, CC BY 4.0; columns
alternateNameId, geonameid, lang, name, isPreferred, isShort, isColloquial, isHistoric,
from, to) and one batched Wikidata SPARQL query (CC0).
"""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from pathlib import Path

import requests

ALT = "https://download.geonames.org/export/dump/alternatenames/{cc}.zip"
WDQS = "https://query.wikidata.org/sparql"
UA = {"User-Agent": "hack-the-pool-2026/0.1 (team research script; Kulturpool hackathon)"}
LPF_CONTEXT = "https://raw.githubusercontent.com/LinkedPasts/linked-places/master/linkedplaces-context-v1.1.jsonld"


def year(value: str) -> int | None:
    m = re.search(r"-?\d{3,4}", value or "")
    return int(m.group()) if m else None


NOW = "2026"


def timespan(start: int | None, end: int | None, ongoing: bool = False) -> dict | None:
    """LPF timespan. LPF reads a missing end as "during the start period" (spec: '{"start":
    {"in":"1832"}} indicates during 1832'), so:
      timespan(1892, 1893)               during 1892-1893 (e.g. an attestation)
      timespan(1995, None, ongoing=True) since 1995, still valid: end {"earliest": NOW}
      timespan(1995, None)               during 1995 only
      timespan(None, 1995)               until 1995, start unknown: start {"latest": "1995"}
    """
    if start is None and end is None:
        return None
    ts: dict = {}
    if start is not None:
        ts["start"] = {"in": str(start)}
    else:
        ts["start"] = {"latest": str(end)}
    if end is not None:
        ts["end"] = {"in": str(end)}
    elif ongoing:
        ts["end"] = {"earliest": NOW}
    return {"timespans": [ts]}


def _bounds(ts: dict) -> tuple[int | None, int | None]:
    """(first year, last year) a timespan may cover; None = unbounded on that side."""
    start, end = ts.get("start", {}), ts.get("end")
    s = year(start.get("in", "") or start.get("earliest", ""))  # start.latest only: unknown start
    if end is None:
        return s, s  # LPF: no end = the interval described by the start
    if "in" in end:
        return s, year(end["in"])
    if "latest" in end:
        return s, year(end["latest"])
    return s, None  # end.earliest only: still valid


def overlaps(when: dict | None, y1: int, y2: int) -> bool | None:
    """Does a name's validity overlap the window [y1, y2]? None if undated."""
    if not when:
        return None
    for ts in when.get("timespans", []):
        s, e = _bounds(ts)
        if (s is None or s <= y2) and (e is None or e >= y1):
            return True
    return False


def is_latin(name: str) -> bool:
    letters = [c for c in name if c.isalpha()]
    return bool(letters) and all("LATIN" in unicodedata.name(c, "") for c in letters)


def geonames_alt_names(geonameids: set[str], countries: set[str], cache: Path) -> dict[str, list]:
    """geonameid → [{toponym, lang, historic, start, end, preferred}] from the per-country files."""
    out: dict[str, list] = {g: [] for g in geonameids}
    cache.mkdir(parents=True, exist_ok=True)
    for cc in sorted(countries):
        path = cache / f"{cc}.zip"
        if not path.exists():
            r = requests.get(ALT.format(cc=cc), timeout=300)
            if r.status_code != 200:
                continue
            path.write_bytes(r.content)
        with zipfile.ZipFile(path) as z, z.open(f"{cc}.txt") as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                if (
                    len(c) < 10
                    or c[1] not in out
                    or c[2] in ("link", "wkdt", "post", "iata", "icao", "faac", "unlc", "abbr")
                    or c[6] == "1"  # colloquial ("Pantruche" for Paris): not a source name
                ):
                    continue
                out[c[1]].append(
                    {
                        "toponym": c[3],
                        "lang": c[2] or None,
                        "historic": c[7] == "1",
                        "preferred": c[4] == "1",
                        "start": year(c[8]),
                        "end": year(c[9]),
                    }
                )
    return out


def wikidata_by_geonames(
    geonameids: list[str], expect: dict[str, str] | None = None
) -> dict[str, dict]:
    """geonameid → {qid, label_de, label_en, official: [{toponym, lang, start, end}],
    other_items}. One POST to the query service; raises on non-200 (no retry loop)."""
    values = " ".join(f'"{g}"' for g in geonameids)
    q = f"""
    SELECT ?gn ?item ?de ?en ?name ?start ?end WHERE {{
      VALUES ?gn {{ {values} }}
      ?item wdt:P1566 ?gn .
      OPTIONAL {{ ?item rdfs:label ?de FILTER(LANG(?de) = "de") }}
      OPTIONAL {{ ?item rdfs:label ?en FILTER(LANG(?en) = "en") }}
      OPTIONAL {{ ?item p:P1448 ?st . ?st ps:P1448 ?name .
                 OPTIONAL {{ ?st pq:P580 ?start }} OPTIONAL {{ ?st pq:P582 ?end }} }}
    }}"""
    r = requests.post(
        WDQS,
        data={"query": q},
        headers={**UA, "Accept": "application/sparql-results+json"},
        timeout=120,
    )
    r.raise_for_status()
    # Several items can claim one GeoNames id (a city and a hospital in it): keep them
    # apart, then pick per id the item whose label matches `expect` (the GeoNames name).
    items: dict[tuple[str, str], dict] = {}
    for b in r.json()["results"]["bindings"]:
        g, qid = b["gn"]["value"], b["item"]["value"].rsplit("/", 1)[-1]
        d = items.setdefault((g, qid), {"qid": qid, "label_de": "", "label_en": "", "official": []})
        d["label_de"] = d["label_de"] or b.get("de", {}).get("value", "")
        d["label_en"] = d["label_en"] or b.get("en", {}).get("value", "")
        if "name" in b:
            n = {
                "toponym": b["name"]["value"],
                "lang": b["name"].get("xml:lang"),
                "start": year(b.get("start", {}).get("value", "")),
                "end": year(b.get("end", {}).get("value", "")),
            }
            if n not in d["official"]:
                d["official"].append(n)
    out: dict[str, dict] = {}
    for g in {g for g, _ in items}:
        cands = [d for (gg, _), d in items.items() if gg == g]
        want = (expect or {}).get(g, "").casefold()

        def score(d: dict, want: str = want) -> tuple:
            labels = {d["label_de"].casefold(), d["label_en"].casefold()}
            return (want in labels, any(want and want in lab for lab in labels), len(d["official"]))

        best = max(cands, key=score)
        out[g] = {**best, "other_items": [d["qid"] for d in cands if d is not best]}
    return out


SEARCH_LANGS = {None, "de", "en", "fr", "it", "nl", "hr", "pt", "la", "es"}
ORDER = ["attested", "official", "dated", "historic", "current", "label"]


def kind_of(name: dict) -> str:
    return name["citations"][0]["label"].rsplit("[", 1)[-1].rstrip("]")


def query_names(feature: dict, y1: int, y2: int, cap: int = 5) -> list[str]:
    """Names to search for a place in the window [y1, y2], from an LPF feature.

    Attested names always count. Other Latin-script names count unless every dated
    statement about that toponym lies outside the window (Mumbai from 1995 is out for
    1892; Batavia 1619-1949 is in; an undated name stays in). Ordered attested →
    official → dated → historic → current → label, capped.
    """
    dated: dict[str, list[bool]] = {}
    for n in feature["names"]:
        ov = overlaps(n.get("when"), y1, y2)
        if ov is not None and kind_of(n) != "attested":
            dated.setdefault(n["toponym"], []).append(ov)
    out = []
    for kind in ORDER:
        for n in feature["names"]:
            t = n["toponym"]
            if kind_of(n) != kind or t in out:
                continue
            if kind != "attested":
                if not is_latin(t) or n.get("lang") not in SEARCH_LANGS:
                    continue
                if t in dated and not any(dated[t]):
                    continue
            out.append(t)
    return out[:cap]
