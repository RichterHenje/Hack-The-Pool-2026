"""Itinerary of SMS Kaiserin Elisabeth (1892-1914) from the team vault → table + map layers.

    uv run python -m scripts.ke_itinerary [vault_dir]

Sources (team vault, read-only):
  Personen/Weltreise Erzherzog Franz Ferdinand ... (1892-1893).md  "#Route" chain of [[places]];
      the chain after "Ab Hier mit einem anderen Passagierschiff" is Franz Ferdinand's
      onward journey WITHOUT the ship (segment "ff_onward", kept apart).
  Schiffe/Kaiserin Elisabeth, Kreuzer.md  later voyages: one segment per dated bullet,
      places in the order they are linked.

Writes prototype/data/:
  ke_itinerary.csv      one row per stop: segment, seq, years, place_note, geo fields
  ke_stops.geojson      geocoded stops (Point)
  ke_routes.geojson     one LineString per segment through its geocoded stops
Stops are in written order; per-stop dates are not in the vault (only segment dates).
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

from kp import geo
from scripts.vault_places import VAULT, wikilinks

OUT = Path("../../3_visualization/web/data")  # the web pages (expedition_pool_edition/3_visualization/web)
WELTREISE = "Personen/Weltreise Erzherzog Franz Ferdinand von Österreich-Este (1892-1893).md"
SHIP = "Schiffe/Kaiserin Elisabeth, Kreuzer.md"
ONWARD = "Ab Hier mit einem anderen Passagierschiff"
# Region notes are context, not stops
# Short labels summarising each dated bullet of the ship note (editorial; raw text otherwise)
LABELS = {
    "voyage_1900_02": "Boxeraufstand, China",
    "voyage_1904_05": "Stationsschiff Ostasien",
    "voyage_1913": "Fahrt nach Ostasien (Kapitän Makovitz)",
    "voyage_1914": "Ostasien bis zur Versenkung bei Tsingtau",
}
REGIONS = {
    "Ostasien",
    "Australien",
    "Mittelmeer",
    "Levante",
    "China",
    "Korea",
    "Nordamerika",
    "Ozeanien und insulares Süd-Ostasien",
    "Literatur",
    "k.u.k Eskader für Ostasien",
}


def weltreise_segments(text: str) -> list[dict]:
    route = text.split("#Route", 1)[1] if "#Route" in text else ""
    ship_part, _, onward = route.partition(ONWARD)
    return [
        {
            "segment": "weltreise_1892_93",
            "label": "Weltreise Franz Ferdinand (an Bord)",
            "years": "1892-12-15/1893",
            "on_ship": True,
            "places": wikilinks(ship_part),
        },
        {
            "segment": "ff_onward_1893",
            "label": "Franz Ferdinand weiter ohne das Schiff",
            "years": "1893",
            "on_ship": False,
            "places": wikilinks(onward),
        },
    ]


YEARS = re.compile(r"1[89]\d\d")


def ship_segments(text: str) -> list[dict]:
    """One segment per bullet that starts with a year; Reise 1 is taken from the
    Weltreise note instead (its line here only names regions)."""
    segs, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("- Reise 1", "- Imperial", "[[Literatur")):
            cur = None
            continue
        years = YEARS.findall(s[:45]) if s.startswith("-") else []
        if years:
            y1, y2 = min(years), max(years)
            seg = f"voyage_{y1}" + (f"_{y2[2:]}" if y2 != y1 else "")
            cur = {
                "segment": seg,
                "label": LABELS.get(seg, re.sub(r"\s+", " ", s.lstrip("- ").split(":")[0])[:60]),
                "years": f"{y1}" if y1 == y2 else f"{y1}-{y2}",
                "on_ship": True,
                "places": [],
            }
            segs.append(cur)
        if cur is not None:
            cur["places"] += [p for p in wikilinks(s) if p not in REGIONS]
    return [s for s in segs if s["places"]]


def main(argv: list[str]) -> int:
    vault = Path(argv[0]) if argv else VAULT
    segs = weltreise_segments((vault / WELTREISE).read_text(encoding="utf-8"))
    segs += ship_segments((vault / SHIP).read_text(encoding="utf-8"))
    # Only place notes are stops: drop links to people and ships (e.g. "Kapitän Franz Mirtl")
    not_places = {p.stem for d in ("Personen", "Schiffe") for p in (vault / d).glob("*.md")}
    not_places |= {t for s in segs for t in s["places"] if t.startswith(("Kapitän", "H.M.S."))}
    for s in segs:
        s["places"] = [p for p in s["places"] if p not in not_places]
    gaz = geo.Gazetteer()
    rows, stops, routes = [], [], []
    for seg in segs:
        coords = []
        for i, place in enumerate(seg["places"], 1):
            m = gaz.lookup(place)
            row = {
                "segment": seg["segment"],
                "label": seg["label"],
                "years": seg["years"],
                "on_ship": seg["on_ship"],
                "seq": i,
                "place_note": place,
                "geo_status": "matched" if m else "unmatched",
                "geo_matched": m["matched"] if m else "",
                "geo_name": m["name"] if m else "",
                "historic_names": "; ".join(geo.historic_names(place)),
                "country": m["country"] if m else "",
                "geonames": m["geonames"] if m else "",
                "ambiguous": m["ambiguous"] if m else "",
                "latitude": m["lat"] if m else "",
                "longitude": m["lon"] if m else "",
            }
            rows.append(row)
            if m:
                coords.append([m["lon"], m["lat"]])
                stops.append(
                    geo.feature(
                        m["lat"],
                        m["lon"],
                        **{k: v for k, v in row.items() if k not in ("latitude", "longitude")},
                    )
                )
        if len(coords) >= 2:
            routes.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {k: seg[k] for k in ("segment", "label", "years", "on_ship")},
                }
            )
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "ke_itinerary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    attr = "Itinerary: team vault Archive_Indien_Schiffreisen; coordinates: GeoNames (CC BY 4.0)"
    geo.write_geojson(stops, OUT / "ke_stops.geojson", attr)
    geo.write_geojson(routes, OUT / "ke_routes.geojson", attr)
    for seg in segs:
        n = [r for r in rows if r["segment"] == seg["segment"]]
        ok = sum(r["geo_status"] == "matched" for r in n)
        print(
            f"{seg['segment']:<20} {seg['years']:<16} {ok:>2}/{len(n):<2} geocoded  {seg['label'][:40]}"
        )
    print(
        f"-> {OUT}/ke_itinerary.csv ({len(rows)} stops), ke_stops.geojson ({len(stops)}), "
        f"ke_routes.geojson ({len(routes)} segments)"
    )
    unmatched = sorted({r["place_note"] for r in rows if r["geo_status"] == "unmatched"})
    print("unmatched:", unmatched)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
