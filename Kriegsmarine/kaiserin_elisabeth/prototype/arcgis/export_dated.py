#!/usr/bin/env python3
"""ArcGIS-/StoryMaps-Export der Reise 1892/93 mit Tagesdaten (nur Standardbibliothek).

Liest die Daten des Prototyps und der Analysen und schreibt neben dieses Skript:
  ke_stops_dated.csv/.geojson  48 Stationen Franz Ferdinands mit Ankunftsdatum, Namen damals/heute
  ke_legs.geojson              47 Etappen als Großkreis, an der Datumsgrenze geteilt
  ke_hunts.csv/.geojson        12 Jagden aus dem Tagebuch
  ke_press.csv/.geojson        automatisch ausgewählte ANNO-Ausschnitte (ungeprüft)
  ke_press_unmatched.csv       Ausschnitte ohne Koordinate (falls es welche gibt)

Aufruf aus diesem Ordner:  python3 export_dated.py
Die Grenzen von 1893 (CShapes 2.0, CC BY-NC-SA) werden bewusst NICHT exportiert.
"""

import csv
import json
import math
import re
from datetime import date
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTO = HERE.parent
KM = PROTO.parent.parent  # Kriegsmarine/
START = date(1892, 12, 15)
VOYAGES = {"Weltreise Franz Ferdinand (an Bord)": "ship", "Franz Ferdinand weiter ohne das Schiff": "onward"}
KIND = {"attested": "belegt", "historic": "historisch", "dated": "datiert", "official": "amtlich"}
# spellings in Höfer's Reiseübersicht for stops whose vault name differs (see Analysen/README.md)
PRINTED = {"Yokohama": ("Jokohama",), "Tokyo": ("Tôkio",), "Kyoto": ("Kiôto",), "Nikko": ("Nikkô",),
           "Delhi": ("Dehli",), "Port Said": ("Port Saïd",), "Hong Kong": ("Hongkong",),
           "Buitenzog": ("Buitenzorg",), "Nouméa": ("Numea",), "Le Havre": ("Havre",)}


def load_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def gn_id(s):
    m = re.search(r"geonames\.org/(\d+)", s or "")
    return m.group(1) if m else None


def iso(d):
    return d.isoformat() if d else ""


def day_index(d):
    return (d - START).days if d else ""


# --- names (Linked Places gazetteer) -------------------------------------------------
def name_history(lpf_path):
    out = {}
    for f in json.loads(lpf_path.read_text(encoding="utf-8"))["features"]:
        gid = next((gn_id(x["identifier"]) for x in f.get("links", []) if gn_id(x["identifier"])), None)
        if not gid:
            continue
        parts, seen = [], set()
        for n in f.get("names", []):
            label = " ".join(c.get("label", "") for c in n.get("citations", []))
            kind = (re.search(r"\[(\w+)\]", label) or [None, ""])[1]
            if kind not in KIND or not re.match(r"^[\x00-ɏ\s'’.-]+$", n["toponym"]):
                continue
            span = ((n.get("when") or {}).get("timespans") or [{}])[0]
            s = (span.get("start") or {}).get("in", "")
            e = (span.get("end") or {}).get("in", "")
            when = f" {s}–{e}".rstrip("–") if s or e else ""
            key = (n["toponym"], kind)
            if key not in seen:
                seen.add(key)
                parts.append(f"{n['toponym']} [{KIND[kind]}{when}]")
        out[gid] = "; ".join(parts[:8])
    return out


# --- stops with dates ------------------------------------------------------------------
def build_stops():
    names = name_history(PROTO / "data" / "ke_places.lpf.json")
    dates = {(r["voyage"], r["seq"]): r for r in load_csv(KM / "Analysen" / "stop_dates.csv")}
    records = {(r["label"], str(r["seq"])): r for r in json.loads(
        (PROTO / "data" / "ke_stop_records.json").read_text(encoding="utf-8"))}
    stops = []
    for f in json.loads((HERE / "ke_stops.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        if p["voyage"] not in VOYAGES:
            continue
        d = dates.get((p["voyage"], str(p["seq"])), {})
        rec = records.get((p["voyage"], str(p["seq"])), {})
        img = next((r for r in rec.get("kp_records", []) if r.get("open") and r.get("image")), None)
        lon, lat = f["geometry"]["coordinates"][:2]
        stops.append({
            "seq": int(p["seq"]), "leg": VOYAGES[p["voyage"]], "on_ship": p.get("on_ship", ""),
            "name_then": p.get("name_then") or p.get("place"), "name_now": p.get("name_now") or "",
            "country": p.get("country") or "", "lon": lon, "lat": lat,
            "hoefer_from": d.get("first_date") or "", "hoefer_to": d.get("last_date") or "",
            "hoefer_printed": d.get("names_as_printed") or "",
            "names_history": names.get(gn_id(p.get("geonames")), ""),
            "kp_hits": p.get("kp_hits") or 0, "kp_search_url": p.get("kp_search_url") or "",
            "kp_example": p.get("kp_example") or "", "kp_example_url": p.get("kp_example_url") or "",
            "kp_licence": p.get("kp_licence") or "",
            "image_url": img["image"] if img else "", "image_title": img["title"] if img else "",
            "image_licence": img["licence"] if img else "", "image_record_url": img["url"] if img else "",
            "wikidata": p.get("wikidata") or "", "geonames": p.get("geonames") or "",
        })
    stops.sort(key=lambda s: (s["leg"] != "ship", s["seq"]))

    # arrival date from Höfer's itinerary, read in route order: the end of the leg into the place
    # or the start of a stay there (stop_dates.csv first_date is the first mention, often the
    # departure towards the place). Stops not found are interpolated below and marked.
    itin = [r for r in load_csv(KM / "Analysen" / "itinerary_1892_93.csv") if r["date_from"]]
    pos, last = 0, None
    for s in stops:
        variants = {v.strip() for v in s["hoefer_printed"].split(";") if v.strip()}
        variants |= {s["name_then"], *PRINTED.get(s["name_then"], ())}
        t, found = None, None
        for k in range(pos, len(itin)):
            r = itin[k]
            if r["to"] in variants:
                t, found = date.fromisoformat(r["date_to"] or r["date_from"]), k
            elif r["stay"] in variants:
                t, found = date.fromisoformat(r["date_from"]), k
            elif last is None and r["from"] in variants:
                t, found = date.fromisoformat(r["date_from"]), k  # Triest: departure, not an arrival
            if found is not None:
                break
        if t and last and t < last:
            t = None
        if t:
            pos, last = found + 1, t
        s["arrival"], s["date_estimated"] = t, 0 if t else 1
    known = [i for i, s in enumerate(stops) if not s["date_estimated"]]
    for i, s in enumerate(stops):
        if not s["date_estimated"]:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        if prev is None:
            s["arrival"] = None  # Pola: home port, before the timeline
        elif nxt is None:
            s["arrival"] = stops[prev]["arrival"]
        else:
            a, b = stops[prev]["arrival"], stops[nxt]["arrival"]
            s["arrival"] = date.fromordinal(round(a.toordinal() + (b.toordinal() - a.toordinal()) * (i - prev) / (nxt - prev)))
    arrivals = [s["arrival"] for s in stops if s["arrival"]]
    assert arrivals == sorted(arrivals), "arrival dates out of order"

    for s in stops:
        dates_txt = (f"Höfer: {s['hoefer_from']} bis {s['hoefer_to']}" if s["hoefer_from"]
                     else "kein Datum bei Höfer")
        if s["date_estimated"] and s["arrival"]:
            dates_txt += f"; Ankunft geschätzt {iso(s['arrival'])}"
        s["title"] = s["name_then"] + (f" (heute {s['name_now']})" if s["name_now"] and s["name_now"] != s["name_then"] else "")
        s["description"] = "; ".join(x for x in (
            dates_txt,
            f"Namen: {s['names_history']}" if s["names_history"] else "",
            f"Kulturpool: {s['kp_hits']} Datensätze" if s["kp_hits"] else "",
        ) if x)
    return stops


# --- legs as great circles, split at the antimeridian --------------------------------------
def great_circle(a, b, step_deg=1.0):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    p1 = (math.cos(lat1) * math.cos(lon1), math.cos(lat1) * math.sin(lon1), math.sin(lat1))
    p2 = (math.cos(lat2) * math.cos(lon2), math.cos(lat2) * math.sin(lon2), math.sin(lat2))
    omega = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(p1, p2)))))
    n = max(1, int(math.degrees(omega) / step_deg))
    pts = []
    for k in range(n + 1):
        f = k / n
        if omega < 1e-9:
            v = p1
        else:
            s1, s2 = math.sin((1 - f) * omega) / math.sin(omega), math.sin(f * omega) / math.sin(omega)
            v = tuple(s1 * x + s2 * y for x, y in zip(p1, p2))
        pts.append([round(math.degrees(math.atan2(v[1], v[0])), 4),
                    round(math.degrees(math.atan2(v[2], math.hypot(v[0], v[1]))), 4)])
    # split where the line jumps across ±180
    parts, cur = [], [pts[0]]
    for p, q in pairwise(pts):
        if abs(q[0] - p[0]) > 180:
            q_shift = q[0] + (360 if p[0] > 0 else -360)
            edge = 180 if p[0] > 0 else -180
            lat_x = p[1] + (q[1] - p[1]) * (edge - p[0]) / (q_shift - p[0])
            cur.append([edge, round(lat_x, 4)])
            parts.append(cur)
            cur = [[-edge, round(lat_x, 4)]]
        cur.append(q)
    parts.append(cur)
    return parts


def build_legs(stops):
    legs = []
    for a, b in pairwise(stops):
        parts = great_circle((a["lon"], a["lat"]), (b["lon"], b["lat"]))
        onward = b["leg"] == "onward"
        legs.append({
            "type": "Feature",
            "geometry": {"type": "MultiLineString", "coordinates": parts},
            "properties": {
                "from_name": a["name_then"], "to_name": b["name_then"],
                "on_ship": "nein" if onward else "ja",
                "date_from": iso(a["arrival"]), "date_to": iso(b["arrival"]),
                "day_from": day_index(a["arrival"]), "day_to": day_index(b["arrival"]),
                "estimated": max(a["date_estimated"], b["date_estimated"]),
                "title": f"{a['name_then']} → {b['name_then']}",
            },
        })
    return legs


# --- hunts and press --------------------------------------------------------------------------
def build_hunts():
    hunts = []
    for f in json.loads((KM / "enrichment" / "data" / "hunts.geojson").read_text(encoding="utf-8"))["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        a, b = date.fromisoformat(p["start"]), date.fromisoformat(p["end"])
        hunts.append({"id": p["id"], "title": p["label"], "date_from": iso(a), "date_to": iso(b),
                      "day_from": day_index(a), "day_to": day_index(b), "animals": p.get("animals", ""),
                      "kill_sentences": p.get("kill_sentences", ""), "photos": p.get("photos", ""),
                      "description": f"{a:%d.%m.%Y}–{b:%d.%m.%Y}: {p.get('animals', '')}", "lon": lon, "lat": lat})
    return hunts


def norm(s):
    return re.sub(r"[^a-zäöü]", "", (s or "").lower())


def build_press(stops, hunts):
    places = {}
    for h in hunts:
        for part in re.split(r"\s*/\s*", h["title"]):
            places.setdefault(norm(re.sub(r"\(.*?\)", "", part)), (h["lon"], h["lat"]))
    for s in stops:
        for n in (s["name_then"], s["name_now"], s["hoefer_printed"]):
            if n:
                places.setdefault(norm(n), (s["lon"], s["lat"]))
    by_episode = {h["id"]: (h["lon"], h["lat"]) for h in hunts}
    rows, unmatched = [], []
    for r in load_csv(PROTO / "data" / "presse_anno.csv"):
        key = norm(r["place"])
        hit = (by_episode.get(r.get("episode", "")) or places.get(key)
               or next((v for k, v in places.items() if key and (key in k or k in key)), None))
        ev = date.fromisoformat(r.get("event_date") or r["date"])
        q = re.sub(r"\s+", " ", r["quote"]).strip()
        row = {"date_published": r["date"], "event_date": iso(ev), "day_index": day_index(ev),
               "newspaper": r["newspaper"], "place": r["place"], "episode": r.get("episode", ""),
               "relevance": r.get("relevance", ""), "quote": q[:1000],
               "page_url": re.sub(r"\?query=[^&]*&", "?", r["page_url"]),
               "title": f"{r['newspaper']}, {r['date']}",
               "status": "automatisch ausgewählt, ungeprüft (OCR)"}
        if hit:
            row["lon"], row["lat"] = hit
            rows.append(row)
        else:
            unmatched.append(row)
    return rows, unmatched


# --- writers ------------------------------------------------------------------------------------
def write_points(name, rows, fields):
    # BOM like ke_stops.csv: ArcGIS Online's CSV import then reads umlauts correctly
    with open(HERE / f"{name}.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["latitude", "longitude", *fields])
        w.writeheader()
        for r in rows:
            w.writerow({"latitude": r["lat"], "longitude": r["lon"], **{k: r.get(k, "") for k in fields}})
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
         "properties": {k: r.get(k, "") for k in fields}} for r in rows]}
    (HERE / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    stops = build_stops()
    for s in stops:
        s["arrival_date"], s["day_index"] = iso(s["arrival"]), day_index(s["arrival"])
    stop_fields = ["seq", "leg", "on_ship", "title", "name_then", "name_now", "country", "arrival_date",
                   "day_index", "date_estimated", "hoefer_from", "hoefer_to", "hoefer_printed", "names_history",
                   "description", "kp_hits", "kp_search_url", "kp_example", "kp_example_url", "kp_licence",
                   "image_url", "image_title", "image_licence", "image_record_url", "wikidata", "geonames"]
    write_points("ke_stops_dated", stops, stop_fields)

    legs = build_legs(stops)
    (HERE / "ke_legs.geojson").write_text(json.dumps(
        {"type": "FeatureCollection", "features": legs}, ensure_ascii=False), encoding="utf-8")

    hunts = build_hunts()
    write_points("ke_hunts", hunts, ["id", "title", "date_from", "date_to", "day_from", "day_to",
                                     "animals", "kill_sentences", "photos", "description"])

    press, unmatched = build_press(stops, hunts)
    press_fields = ["title", "date_published", "event_date", "day_index", "newspaper", "place", "episode",
                    "relevance", "quote", "page_url", "status"]
    write_points("ke_press", press, press_fields)
    if unmatched:
        with open(HERE / "ke_press_unmatched.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=press_fields)
            w.writeheader()
            w.writerows({k: r.get(k, "") for k in press_fields} for r in unmatched)

    split = sum(1 for leg in legs if len(leg["geometry"]["coordinates"]) > 1)
    print(f"stops {len(stops)} (estimated {sum(s['date_estimated'] for s in stops)}, "
          f"with open image {sum(1 for s in stops if s['image_url'])}), legs {len(legs)} "
          f"(split at ±180: {split}), hunts {len(hunts)}, press {len(press)} placed / {len(unmatched)} unplaced")


if __name__ == "__main__":
    main()
