"""ArcGIS Online upload pack for the SMS Kaiserin Elisabeth prototype.

    uv run python -m scripts.ke_arcgis_pack

Reads prototype/data/ke_stop_records.json, ke_routes.geojson, ke_places.lpf.json and
writes prototype/arcgis/ (tracked):
  ke_stops.geojson / ke_stops.csv   one point per stop, flat fields for popups, and
                                    date_from / date_to (ISO) so the layer can be
                                    time-enabled (time slider)
  ke_routes.geojson                 one line per segment with the same time fields
Fields are short and flat: ArcGIS shows them directly in popups and the attribute table.
Dates are segment dates (per-stop dates are not in the vault): the slider steps by voyage.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

DATA = Path("../../3_visualization/web/data")
OUT = Path("../../3_visualization/arcgis/layers")

# Segment dates only as the vault states them; year-only statements span the year.
# The two notes disagree on the world tour: ship note 12.12.1892-19.12.1893 (the ship's
# voyage), Weltreise note 15.12.1892-18.10.1893 (Franz Ferdinand's journey).
SEGMENT_DATES = {
    "weltreise_1892_93": ("1892-12-12", "1893-12-19", "Schiffsnotiz: Reise 1"),
    "ff_onward_1893": ("", "1893-10-18", "Weltreise-Notiz: Rückkehr; Beginn nicht notiert"),
    "voyage_1900_02": ("1900-01-01", "1902-12-31", "Schiffsnotiz: 1900-1902"),
    "voyage_1904_05": ("1904-01-02", "1905-12-06", "Schiffsnotiz: 02.01.1904-06.12.1905"),
    "voyage_1913": ("1913-01-01", "1913-12-31", "Schiffsnotiz: 1913"),
    "voyage_1914": ("1914-01-01", "1914-11-02", "Schiffsnotiz: 1914, versenkt 02.11.1914"),
}


def main() -> int:
    stops = json.loads((DATA / "ke_stop_records.json").read_text(encoding="utf-8"))
    lpf = json.loads((DATA / "ke_places.lpf.json").read_text(encoding="utf-8"))
    places = {f["properties"]["title"]: f for f in lpf["features"]}
    feats, rows = [], []
    for s in stops:
        d_from, d_to, d_src = SEGMENT_DATES.get(s["segment"], ("", "", ""))
        f = places.get(s["place_note"], {})
        names = [n for n in f.get("names", []) if "[attested]" in n["citations"][0]["label"]]
        wd = next(
            (lk["identifier"] for lk in f.get("links", []) if "wikidata" in lk["identifier"]), ""
        )
        top = s["kp_records"][0] if s["kp_records"] else {}
        q = " ".join(f'"{n}"' for n in s["query_names"][:1])
        props = {
            "seq": int(s["seq"]),
            "place": s["place_note"][:120],
            "name_then": ", ".join(n["toponym"] for n in names)[:80],
            "name_now": s["geo_name"],
            "country": s["country"],
            "voyage": s["label"],
            "on_ship": "ja" if str(s["on_ship"]) == "True" else "nein",
            "date_from": d_from,
            "date_to": d_to,
            "date_source": d_src,
            "kp_window": s["window"],
            "kp_hits": int(s["kp_found"]),
            "kp_example": (top.get("title") or "")[:200],
            "kp_example_url": top.get("url", ""),
            "kp_licence": top.get("licence", ""),
            "kp_search_url": "https://kulturpool.at/suche?query=" + re.sub(r"\s+", "+", q) if q else "",
            "geonames": s["geonames"],
            "wikidata": wd,
        }
        lat, lon = float(s["latitude"]), float(s["longitude"])
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props,
            }
        )
        rows.append({"latitude": lat, "longitude": lon, **props})

    routes = json.loads((DATA / "ke_routes.geojson").read_text(encoding="utf-8"))
    for r in routes["features"]:
        p = r["properties"]
        d_from, d_to, d_src = SEGMENT_DATES.get(p["segment"], ("", "", ""))
        r["properties"] = {
            "voyage": p["label"],
            "on_ship": "ja" if p["on_ship"] else "nein",
            "date_from": d_from,
            "date_to": d_to,
            "date_source": d_src,
            "segment": p["segment"],
        }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ke_stops.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "ke_routes.geojson").write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": routes["features"]}, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    with (OUT / "ke_stops.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(
        f"-> {OUT}/ke_stops.geojson ({len(feats)} points), ke_stops.csv, "
        f"ke_routes.geojson ({len(routes['features'])} lines)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
