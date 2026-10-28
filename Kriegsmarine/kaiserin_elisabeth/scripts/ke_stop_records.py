"""Kulturpool records per itinerary stop, time-boxed to the segment's years (±2).

    uv run python -m scripts.ke_stop_records

For each stop in prototype/data/ke_itinerary.csv, search Kulturpool for the place as an
exact phrase (historic and modern name: "Bombay" and "Mumbai"), filtered to records
dated within the segment's years ±2 (dateMin/dateMax). These are records that MENTION
the place in that period, not objects from the voyage ("Colombo" also finds Columbus):
the page labels them so. Images are shown only for records whose rights are all OPEN.

Also writes prototype/data/ke_data.js (window.KE = {...}) bundling routes, stops and
records, so prototype/schiff.html works from disk and on GitHub Pages without a server.
"""

from __future__ import annotations

import calendar
import csv
import datetime as dt
import json
import re
from pathlib import Path

from kp import kulturpool as kpa
from kp import places, rights

DATA = Path("prototype/data")
MARGIN = 2
SHIP_QUERIES = [
    '"SMS Kaiserin Elisabeth"',
    '"S.M.S. Kaiserin Elisabeth"',
    '"Kaiserin Elisabeth" Kreuzer',
]


def ts(year: int) -> int:
    return calendar.timegm(dt.datetime(year, 1, 1).timetuple())


def year_range(years: str) -> tuple[int, int]:
    ys = [int(y) for y in re.findall(r"1[89]\d\d", years)]
    return min(ys) - MARGIN, max(ys) + MARGIN


def record(d: dict) -> dict:
    return {
        "id": d["id"],
        "title": (d.get("title") or "")[:140],
        "provider": d.get("dataProvider", ""),
        "date": ", ".join(d.get("date") or [])[:40],
        "licence": rights.label(d),
        "open": rights.is_open(d),
        "image": d.get("previewImage", "") if rights.is_open(d) else "",
        "url": d.get("url", ""),
    }


def stop_records(names: list[str], y1: int, y2: int, n: int = 6) -> tuple[int, list[dict]]:
    """One exact-phrase query per name, merged. found = largest single-name count
    (a lower bound for the union; records may mention both names)."""
    flt = f"dateMin:>={ts(y1)} && dateMax:<{ts(y2 + 1)}"
    found, recs = 0, {}
    for x in names:
        res = kpa.search(f'"{x}"', per_page=n, filter_by=flt)
        found = max(found, res["found"])
        for d in kpa.docs(res):
            recs.setdefault(d["id"], record(d))
    return found, list(recs.values())[:n]


def main() -> int:
    rows = list(csv.DictReader((DATA / "ke_itinerary.csv").open(encoding="utf-8")))
    lpf_path = DATA / "ke_places.lpf.json"
    lpf = {}
    if lpf_path.exists():
        fc = json.loads(lpf_path.read_text(encoding="utf-8"))
        lpf = {f["properties"]["title"]: f for f in fc["features"]}
    cache: dict[tuple, tuple[int, list]] = {}
    out = []
    for r in rows:
        if r["geo_status"] != "matched":
            continue
        y1, y2 = year_range(r["years"])
        if r["place_note"] in lpf:
            # Period-valid names from the historic gazetteer (scripts/ke_places_lpf.py)
            names = places.query_names(lpf[r["place_note"]], y1, y2)
        else:
            # Fallback: matched name, GeoNames name, stated period names
            hist = [h for h in r["historic_names"].split("; ") if h]
            names = list(dict.fromkeys([r["geo_matched"], r["geo_name"], *hist]))
        key = (tuple(names), y1, y2)
        if key not in cache:
            cache[key] = stop_records(names, y1, y2)
        found, recs = cache[key]
        out.append(
            {
                **r,
                "query_names": names,
                "window": f"{y1}-{y2}",
                "kp_found": found,
                "kp_records": recs,
            }
        )
        print(f"{r['segment']:<18} {r['place_note'][:32]:<32} {y1}-{y2} {found:>5}")

    ship = {}
    for q in SHIP_QUERIES:
        res = kpa.search(q, per_page=10)
        for d in kpa.docs(res):
            ship[d["id"]] = record(d)
    (DATA / "ke_stop_records.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # Compact name history per place for the page: attested + dated/historic Latin names
    names = {}
    for title, f in lpf.items():
        keep = []
        for n in f["names"]:
            kind = places.kind_of(n)
            if kind in ("label", "current") or not places.is_latin(n["toponym"]):
                continue
            if kind != "attested" and n.get("lang") not in places.SEARCH_LANGS:
                continue  # keep the popup readable: languages the search uses
            ts = (n.get("when") or {}).get("timespans", [{}])[0]
            keep.append(
                {
                    "name": n["toponym"],
                    "lang": n.get("lang") or "",
                    "kind": kind,
                    "from": ts.get("start", {}).get("in", ""),
                    "to": ts.get("end", {}).get("in", "") if ts.get("end") else "",
                }
            )
        names[title] = {
            "names": keep[:12],
            "links": [lk["identifier"] for lk in f["links"]],
        }

    unmatched = [r["place_note"] for r in rows if r["geo_status"] != "matched"]
    bundle = {
        "routes": json.loads((DATA / "ke_routes.geojson").read_text(encoding="utf-8")),
        "stops": out,
        "places": names,
        "unmapped": sorted(set(unmatched)),
        "n_itinerary_stops": len(rows),
        "ship_records": list(ship.values()),
        "generated": dt.date.today().isoformat(),
        "attribution": "Itinerary: team vault (khm-team); coordinates: GeoNames CC BY 4.0; "
        "records: Kulturpool, rights per record",
    }
    (DATA / "ke_data.js").write_text(
        "window.KE = " + json.dumps(bundle, ensure_ascii=False) + ";\n", encoding="utf-8"
    )
    print(
        f"-> {DATA}/ke_stop_records.json ({len(out)} stops), ke_data.js; ship records: {len(ship)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
