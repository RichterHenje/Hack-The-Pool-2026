"""Step 0: places – start from the normalised route and add Wikidata identifiers and coordinates.

Inputs
  ../normalization/json/ortschaften.json  route places of the voyage, from the vault (filter_voyage.py):
                                          vault id, note title, position(s) on the route
  route_wikidata.json                     QID per vault note (looked up 27.10.2026), optional fixed
                                          point + coord_note where Wikidata has none or is too coarse
  places.json                             enrichment overlay for the hunting places: diary/OCR
                                          spellings, ANNO search terms, region (episode grouping)

Coordinates are read from Wikidata (P625) here, not typed in; a fixed lat/lon in route_wikidata.json
or places.json is used only where a coord_note explains why.

Output
  data/route_places.json, data/route.geojson   the whole route (Lisa's 49 places), for the map
  data/places_resolved.json                    the hunting places with vault ids + coordinates,
                                               used by the following steps
"""
import json

from common import ROOT, get_json, save

NORM = ROOT.parent / "normalization" / "json"
WD = "https://www.wikidata.org/w/api.php"


def wikidata(qids):
    out = {}
    qids = sorted({q for q in qids if q})
    for i in range(0, len(qids), 50):
        r = get_json(WD, {"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]),
                          "props": "labels|claims", "languages": "de|en", "format": "json"})
        for q, e in r["entities"].items():
            c = e.get("claims", {}).get("P625")
            v = c[0]["mainsnak"].get("datavalue", {}).get("value") if c else None
            labels = e.get("labels", {})
            out[q] = {"label": (labels.get("de") or labels.get("en") or {}).get("value"),
                      "lat": round(v["latitude"], 4) if v else None, "lon": round(v["longitude"], 4) if v else None}
    return out


def note_title(place):
    return place["_meta"]["datei"].split("/", 1)[1].removesuffix(".md")


def main():
    route = json.loads((NORM / "ortschaften.json").read_text())
    qmap = json.loads((ROOT / "route_wikidata.json").read_text())
    overlay = json.loads((ROOT / "places.json").read_text())
    wd = wikidata([v["wikidata"] for v in qmap.values()] + [p["wikidata"] for p in overlay])

    def coords(qid, fixed):
        if fixed.get("lat") is not None:
            return fixed["lat"], fixed["lon"], "fixed"
        if qid and wd.get(qid, {}).get("lat") is not None:
            return wd[qid]["lat"], wd[qid]["lon"], "wikidata"
        return None, None, None

    places = []
    for p in route:
        t = note_title(p)
        m = qmap.get(t, {})
        lat, lon, how = coords(m.get("wikidata"), m)
        places.append({
            "vault_id": p["_meta"]["id"], "vault_note": t, "label": p["Ort"],
            "route_positions": p["Position auf der Route"],
            "wikidata": m.get("wikidata"), "wikidata_label": wd.get(m.get("wikidata"), {}).get("label"),
            "lat": lat, "lon": lon, "coords_from": how, "coord_note": m.get("coord_note"),
        })
    places.sort(key=lambda x: min(x["route_positions"]))
    save("route_places.json", {"source": "normalization/json/ortschaften.json + Wikidata", "places": places})
    stops = sorted(((pos, x) for x in places for pos in x["route_positions"] if x["lat"] is not None), key=lambda s: s[0])
    save("route.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[x["lon"], x["lat"]] for _, x in stops]},
         "properties": {"name": "Route der Weltreise laut Vault (Reihenfolge der Ortsnotizen)"}}] + [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [x["lon"], x["lat"]]},
         "properties": {k: x[k] for k in ("vault_id", "label", "route_positions", "wikidata", "coord_note")}}
        for x in places if x["lat"] is not None]})

    ids = {x["vault_note"]: x["vault_id"] for x in places}
    resolved = []
    for o in overlay:
        lat, lon, how = coords(o["wikidata"], o if o.get("coord_note") else {})
        resolved.append(o | {"lat": lat, "lon": lon, "coords_from": how,
                             "vault": [{"note": v, "id": ids.get(v)} for v in o["vault"]],
                             "on_route": any(v in ids for v in o["vault"])})
    save("places_resolved.json", resolved)
    print(f"route: {len(places)} places, {sum(x['lat'] is not None for x in places)} with coordinates; "
          f"hunting places: {len(resolved)}, {sum(r['on_route'] for r in resolved)} on the normalised route")
    for x in places:
        if x["lat"] is None or x["coord_note"]:
            print(f"   {x['label']:<45} {x['wikidata'] or '-':<10} {x['coord_note'] or ''}")


if __name__ == "__main__":
    main()
