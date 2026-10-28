"""Map layer from an Obsidian vault's place notes (team vault: Archive_Indien_Schiffreisen).

    uv run python -m scripts.vault_places [vault_dir] [--gnd]

Reads <vault>/Ortschaften/*.md (template notes "0_Muster*" skipped), geocodes each note
title with kp.geo.Gazetteer (modern name from "heut. ..." first; a named country must
agree), and counts the vault notes that link to each place ([[...]] backlinks) by folder.
With --gnd it also asks lobid-gnd for a GND place suggestion per note.

Every value it adds is a PROPOSAL for the note template's "Geonames" / "GND" fields:
check before copying it into a note. Output in maps/ (tracked):
  kriegsmarine_ortschaften.geojson   points with coordinates
  kriegsmarine_ortschaften.csv       all notes, with geo_status
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

import requests

from kp import geo

# The vault next to this folder (team repo layout) or a local clone of the team branch
_VAULT_CANDIDATES = [
    Path("../../1_sources/Vault/Archive_Indien_Schiffreisen"),  # team repo: expedition_pool_edition/2_processing/kaiserin_elisabeth/
    Path("../Vault/Archive_Indien_Schiffreisen"),  # earlier layout: Kriegsmarine/kaiserin_elisabeth/
    Path("../Kriegsmarine/Vault/Archive_Indien_Schiffreisen"),
    Path("reference/team-khm/Kriegsmarine/Vault/Archive_Indien_Schiffreisen"),
]
VAULT = next((p for p in _VAULT_CANDIDATES if p.is_dir()), _VAULT_CANDIDATES[-1])
OUT = Path("maps")
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def wikilinks(text: str) -> list[str]:
    """Targets of [[Note]], [[Note|alias]], [[Note#heading]] links."""
    return [m.strip() for m in LINK.findall(text)]


def backlinks(vault: Path) -> dict[str, collections.Counter]:
    """target note title -> Counter of linking folders (self-links and repeats not counted)."""
    out: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for md in vault.rglob("*.md"):
        folder = md.parent.name if md.parent != vault else "(root)"
        for t in set(wikilinks(md.read_text(encoding="utf-8", errors="replace"))):
            if t != md.stem:
                out[t][folder] += 1
    return out


def gnd_suggestion(name: str) -> tuple[str, str]:
    """Top lobid-gnd place hit for a name: (GND IRI, preferred name), or ('', '')."""
    q = geo.name_parts(name)[0]
    r = requests.get(
        "https://lobid.org/gnd/search",
        params={"q": q, "filter": "type:PlaceOrGeographicName", "format": "json", "size": 1},
        timeout=30,
    )
    if r.ok and r.json().get("member"):
        m = r.json()["member"][0]
        return m.get("id", ""), m.get("preferredName", "")
    return "", ""


def main(argv: list[str]) -> int:
    vault = Path(next((a for a in argv if not a.startswith("--")), VAULT))
    places_dir = vault / "Ortschaften"
    if not places_dir.is_dir():
        print(f"no Ortschaften folder in {vault}")
        return 1
    notes = sorted(p for p in places_dir.glob("*.md") if not p.stem.startswith("0_Muster"))
    links = backlinks(vault)
    gaz = geo.Gazetteer()
    rows = []
    for note in notes:
        name = note.stem
        m = gaz.lookup(name)
        bl = links.get(name, collections.Counter())
        row = {
            "note": name,
            "geo_status": "unmatched",
            "geo_matched": "",
            "geo_name": "",
            "country": "",
            "geo_ambiguous": "",
            "geonames": "",
            "latitude": "",
            "longitude": "",
            "links_in": sum(bl.values()),
            "links_by_folder": "; ".join(f"{k} {v}" for k, v in bl.most_common()),
            "links_out": "; ".join(wikilinks(note.read_text(encoding="utf-8", errors="replace"))),
        }
        if m:
            row.update(
                geo_status="matched" if m["matched"] == geo.name_parts(name)[0] else "part",
                geo_matched=m["matched"],
                geo_name=m["name"],
                country=m["country"],
                geo_ambiguous=m["ambiguous"],
                geonames=m["geonames"],
                latitude=m["lat"],
                longitude=m["lon"],
            )
        elif geo.norm(geo.name_parts(name)[0]) in geo.COUNTRIES:
            row["geo_status"] = "country"
        if "--gnd" in argv:
            row["gnd_suggestion"], row["gnd_label"] = gnd_suggestion(name)
        rows.append(row)

    OUT.mkdir(exist_ok=True)
    with (OUT / "kriegsmarine_ortschaften.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    feats = [
        geo.feature(
            r["latitude"],
            r["longitude"],
            **{k: v for k, v in r.items() if k not in ("latitude", "longitude")},
        )
        for r in rows
        if r["latitude"] != ""
    ]
    geo.write_geojson(
        feats,
        OUT / "kriegsmarine_ortschaften.geojson",
        "Places: team vault Archive_Indien_Schiffreisen; coordinates: GeoNames (CC BY 4.0)",
    )
    st = collections.Counter(r["geo_status"] for r in rows)
    print(f"{len(rows)} place notes: " + ", ".join(f"{k} {v}" for k, v in st.most_common()))
    print(f"-> {OUT}/kriegsmarine_ortschaften.geojson ({len(feats)} points) + .csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
