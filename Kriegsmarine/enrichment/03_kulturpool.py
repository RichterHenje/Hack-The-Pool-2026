"""Step 3: related objects from Kulturpool (https://api.kulturpool.at/docs).

Two kinds of results, kept apart on purpose:
  direct  - records whose title/description refers to FF's voyage, its people or its
            collections (seed searches, then one hop of /v2/similar?on=metadata, then a
            regex check on the text). Mostly NHM Intendanzakten, ÖNB prints, medals.
  context - objects about the hunting regions (place names, with image), NOT evidence
            about FF; shown as "from the collections" next to an episode.

Output: data/kulturpool.json
"""
import json
import re

from common import ROOT, get_json, load, save

API = "https://api.kulturpool.at/v2"
PLACES = {p["id"]: p for p in load("places_resolved.json")}

SEEDS = [
    "Franz Ferdinand Weltreise", "Erzherzog Franz Ferdinand", "Kaiserin Elisabeth Schiff",
    "Weltreise Erzherzog Sammlung", "Lorenz Liburnau", "Ludwig Lorenz Intendanz",
    "Sammlung des Erzherzogs", "Franz Ferdinand Indien",
]
SIMILAR_HOPS_FROM = 12  # direct hits used as seeds for /v2/similar
DIRECT = re.compile(  # voyage-specific wording only; plain "Franz Ferdinand" matches every portrait
    r"Weltreise Seiner kaiserlichen Hoheit|Franz Ferdinand.{0,120}Weltreise|Weltreise.{0,120}Franz Ferdinand|"
    r"Schiff Kaiserin Elisabeth|Ludwig (Ritter )?Lorenz|Dr\. (Ludwig )?Lorenz|Direktor Lorenz|"
    r"Sammlung des Erzherzogs|Imperial Sightseeing|Indienreise.{0,80}Franz Ferdinand", re.I)
NOT_DIRECT = re.compile(r"Erzherzog (Leopold|Rainer|Ludwig Salvator|Karl)|Ferdinand von Tirol|Regiments? Nr|Infanterie|Teisseyre", re.I)
VOYAGE_YEARS = range(1892, 1900)
CONTEXT_PROVIDERS = [
    "Universität Wien", "Naturhistorisches Museum Wien", "Österreichische Nationalbibliothek",
    "Wien Museum", "MAK - Museum für angewandte Kunst, Wien", "Österreichische Galerie Belvedere",
    "Albertina", "Technisches Museum Wien", "Volkskundemuseum Wien",
]
YEAR_1914 = -1767225600  # 1914-01-01 as epoch seconds


def text_of(x):
    return " ".join([x.get("title") or ""] + (x.get("description") or []))


def year_of(x):
    """Year from the date field, else from an NHM file number like 'Aktenzahl Z.196/1893'."""
    m = re.search(r"\b(1[89]\d\d|20\d\d)", " ".join(x.get("date") or []))
    m = m or re.search(r"Z\.[\d.a-zA-Z]+/(\d{4})", x.get("title") or "")
    return int(m.group(1)) if m else None


def tier(x):
    y = year_of(x)
    if y is None or y in VOYAGE_YEARS:
        return "voyage"
    return "modern" if y >= 1990 else None


def record(x, how):
    return {
        "id": x["id"], "title": x.get("title"), "provider": x.get("dataProvider"),
        "description": (x.get("description") or [""])[0][:600], "date": x.get("date"),
        "spatial": x.get("spatial"), "type": x.get("dcType") or x.get("edmType"),
        "url": x.get("url") or f"https://kulturpool.at/objekte/{x['id']}",
        "isShownAt": x.get("isShownAt"), "image": x.get("previewImage"), "iiif": x.get("iiifManifest"),
        "rights": (x.get("edmRightsName") or [None])[0], "found_by": how,
        "year": year_of(x), "tier": tier(x),
    }


def search(q, per_page=30, **extra):
    return [h["document"] for h in get_json(f"{API}/search", {"q": q, "per_page": per_page, **extra}).get("hits", [])]


def direct_objects():
    found = {}
    for q in SEEDS:
        for x in search(q):
            t = text_of(x)
            if DIRECT.search(t) and not NOT_DIRECT.search(t) and tier(x):
                found.setdefault(x["id"], record(x, f"search: {q}"))
    for seed in list(found.values())[:SIMILAR_HOPS_FROM]:
        for h in get_json(f"{API}/similar", {"id": seed["id"], "on": "metadata", "per_page": 20}).get("hits", []):
            x = h["document"]
            t = text_of(x)
            if x["id"] not in found and DIRECT.search(t) and not NOT_DIRECT.search(t) and tier(x):
                found[x["id"]] = record(x, f"similar to {seed['id']}")
    return list(found.values())


def place_matches(obj, place_ids):
    t = text_of({"title": obj["title"], "description": [obj["description"]]}) + " " + " ".join(obj.get("spatial") or [])
    return any(re.search(rf"\b{re.escape(term)}\b", t, re.I)
               for p in place_ids for term in PLACES[p]["anno"] + [PLACES[p]["label"].split(" (")[0]])


def context_objects(h, per_episode=6):
    terms = list(dict.fromkeys(t for p in h["place_ids"] for t in PLACES[p]["anno"]
                               if t not in ("Australien", "Java", "Canada")))[:3]
    provider_filter = "dataProvider:=[" + ",".join(f"`{p}`" for p in CONTEXT_PROVIDERS) + "]"
    seen, out = set(), []
    for term in terms:
        for x in search(term, per_page=40, filter_by=provider_filter):
            if x["id"] in seen or not x.get("previewImage"):
                continue
            seen.add(x["id"])
            old = x.get("dateMin") is None or x["dateMin"] < YEAR_1914
            if old and re.search(rf"\b{re.escape(term)}\b", text_of(x) + " ".join(x.get("spatial") or []), re.I):
                out.append(record(x, f"context: {term}"))
    return out[:per_episode]


def main():
    hunts = load("hunts.json")
    anno_ids = {e["hunt_id"] for e in load("anno.json")["episodes"]}
    direct = direct_objects()
    print(f"direct: {len(direct)}")
    for d in direct:
        print(f"   {d['tier']:<7} {d['year'] or '':<5} {d['provider'][:22]:<22} {d['description'][:70] or d['title'][:70]}")
    episodes = []
    for h in hunts:
        if h["id"] not in anno_ids:
            continue
        linked = [d["id"] for d in direct if place_matches(d, h["place_ids"])]
        ctx = context_objects(h)
        print(f"  {h['id']:<32} direct={len(linked)} context={len(ctx)}")
        episodes.append({"hunt_id": h["id"], "direct": linked, "context": ctx})
    save("kulturpool.json", {
        "source": "Kulturpool (https://kulturpool.at), API https://api.kulturpool.at/v2",
        "direct": direct, "episodes": episodes,
    })


if __name__ == "__main__":
    main()
