"""Step 4: merge diary hunts + ANNO + Kulturpool + photos + people + objects into one file per episode for the web app.

Output: data/enrichment.json (full), data/hunts.geojson (one point per episode)
"""
import json

from common import ROOT, load, save

ANIMALS = {a["id"]: a for a in json.loads((ROOT / "animals.json").read_text())}
PLACES = {p["id"]: p for p in load("places_resolved.json")}
ARTICLES_PER_EPISODE = 10


def place(pid):
    """Hunting place with Wikidata coordinates and vault ids (00_places.py, from normalization/)."""
    p = PLACES[pid]
    return {k: p.get(k) for k in ("id", "label", "lat", "lon", "wikidata", "coord_note", "vault", "on_route")}


def main():
    hunts = {h["id"]: h for h in load("hunts.json")}
    anno = load("anno.json")
    kp = load("kulturpool.json")
    kp_direct = {d["id"]: d for d in kp["direct"]}
    kp_eps = {e["hunt_id"]: e for e in kp["episodes"]}
    hp = {e["hunt_id"]: e for e in load("hoefer_photos.json")["episodes"]}
    people = load("people.json")["people"]
    objects = [o for o in load("objects.json")["objects"] if o["strength"] in ("strong", "medium")]

    episodes = []
    for a in anno["episodes"]:
        h = hunts[a["hunt_id"]]
        articles = [d for d in a["documents"] if d.get("relevance") in ("high", "medium") and d.get("snippets")]
        k = kp_eps.get(h["id"], {"direct": [], "context": []})
        episodes.append({
            "id": h["id"], "region": h["region"], "start": h["start"], "end": h["end"],
            "places": [place(p) for p in h["place_ids"]],
            "animals": [{"id": i, "label_de": ANIMALS[i]["de"], "label_en": ANIMALS[i]["en"], "mentions": n}
                        for i, n in h["animals"].items()],
            "diary": {"entries": h["diary"], "kill_sentences": h["kill_sentences"], "quotes": h["quotes"]},
            "anno": {
                "window": a["window"], "queries": a["queries"],
                "issues_found": len(a["documents"]),
                "issues_high": sum(d.get("relevance") == "high" for d in a["documents"]),
                "articles": articles[:ARTICLES_PER_EPISODE],
            },
            "kulturpool": {"direct": [kp_direct[i] for i in k["direct"]], "context": k["context"]},
            "hoefer": hp.get(h["id"], {}).get("hoefer"),
            "photos": hp.get(h["id"], {}).get("photos", []),
            # objects of the Este collection acquired or described at this stop during the episode's stay
            "objects": [{k: o[k] for k in ("id", "inventory", "type", "title", "url", "strength")}
                        | {"evidence": (o["diary"][0] if o["diary"] else None), "card": o["card"]}
                        for o in objects if h["id"] in o["hunts_here"]][:12],
            "people": sorted(({"id": x["id"], "name": x["name"], "group": x["group"],
                               "kill_sentences": x["diary"]["kills_by_hunt"][h["id"]],
                               "gnd": x["gnd"]["url"], "wikidata": x["wikidata"]}
                              for x in people if h["id"] in x["diary"]["kills_by_hunt"]),
                             key=lambda x: -x["kill_sentences"]),
        })
    episodes.sort(key=lambda e: e["start"])

    save("enrichment.json", {
        "meta": {
            "title": "Franz Ferdinand's hunts on the voyage of S.M.S. Kaiserin Elisabeth 1892/93 – reception",
            "sources": {
                "diary": "Franz Ferdinand, Tagebuch meiner Reise um die Erde 1892–1893, 2 Bde., Wien 1895/96 "
                         "(Internet Archive OCR, uncorrected)",
                "anno": anno["source"], "kulturpool": kp["source"],
            },
            "method": "see enrichment/README.md",
        },
        "episodes": episodes,
        "voyage": {
            "objects_strong": [o for o in load("objects.json")["objects"] if o["strength"] == "strong"],
            "kulturpool": kp["direct"],
            "anno_coverage": anno["coverage"],
            "anno_topics": [t | {"documents": [d for d in t["documents"] if d.get("snippets")][:12]}
                            for t in anno["topics"]],
        },
    })

    features = []
    for e in episodes:
        p = e["places"][0]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
            "properties": {
                "id": e["id"], "label": " / ".join(x["label"] for x in e["places"]),
                "start": e["start"], "end": e["end"],
                "animals": ", ".join(a["label_de"] for a in e["animals"][:4]),
                "kill_sentences": e["diary"]["kill_sentences"],
                "newspaper_issues_high": e["anno"]["issues_high"],
                "kulturpool_direct": len(e["kulturpool"]["direct"]),
                "photos": len(e["photos"]),
                "vault_ids": ", ".join(v["id"] for p in e["places"] for v in p["vault"] if v["id"]),
            },
        })
    save("hunts.geojson", {"type": "FeatureCollection", "features": features})


if __name__ == "__main__":
    main()
