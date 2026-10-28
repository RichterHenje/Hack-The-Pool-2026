"""Step 8: bundle the enrichment for the prototype page reise.html.

Target: ../kaiserin_elisabeth/prototype/data/ke_enrichment.js (window.KEE = {...})

The day spine is the normalised diary (normalization/json/tagebuch_tage.json, 309 days),
not the 170 OCR entries of ke_diary.json. Coordinates per day (`coords`), first match wins:
  hunt     – the day's place (destination of a transfer) names a hunting place of places.json
             (Wikidata coordinates, curated; overrides the gazetteer, which put Katni into India)
  heading  – the prototype gazetteer located the diary heading of that very day (ke_diary.json)
  site     – another day with the same place name (franzferdinandsworld.com) was located that way
  wikidata – the place name matches a route place (route_places.json)
  hand     – HAND below: stops off the vault route, approximate town coordinates
Days at sea and places not found stay without coordinates (list only, no map point).
Everything else is taken from data/*.json as built by steps 00–07; nothing is fetched here.
"""
import html
import json
import re
import unicodedata

from common import ROOT, load

PROTO = ROOT.parent / "kaiserin_elisabeth" / "prototype" / "data"
TARGET = PROTO / "ke_enrichment.js"
DAYS = ROOT.parent / "normalization" / "json" / "tagebuch_tage.json"
ANIMALS = json.loads((ROOT / "animals.json").read_text(encoding="utf-8"))
AUTO = "auto:"
# Stops on land that neither the gazetteer nor Wikidata resolve (approximate town coordinates)
HAND = {
    "trieste": (45.6503, 13.7703), "vienna": (48.2082, 16.3738), "stuttgart": (48.7758, 9.1829),
    "ismailia": (30.5965, 32.2715), "jhansi": (25.4484, 78.5685), "benares": (25.3176, 82.9739),
    "lucknow": (26.8467, 80.9462), "kuching": (1.5535, 110.3593), "tanggeng": (-7.18, 107.07),
    "sindangbarang": (-7.45, 107.13), "nara": (34.6851, 135.8048), "osaka": (34.6937, 135.5023),
    "miyajima": (34.2959, 132.3199), "revelstoke": (50.998, -118.196), "spokane": (47.6588, -117.426),
    "livingston": (45.6619, -110.5605), "buttecity": (46.0038, -112.5348),
    "mammothhotspringshotel": (44.977, -110.700), "fountaingeyserhotel": (44.553, -110.833),
    "yellowstonelakehotel": (44.550, -110.400), "grandcanonhotel": (44.720, -110.490),
    "manitousprings": (38.8597, -104.9172), "manitou": (38.8597, -104.9172),
    # Place names given by the team for days the site names differently (Wikidata P625, 27.10.2026)
    "sikanderaba": (17.45, 78.5),                   # 27.01. Secunderabad, Q1003502 (diary: „Sikandarabad“)
    "portkennedyandsomersetbay": (-10.5789, 142.22),  # 06.05. „Kenneby Bay“: Port Kennedy, Thursday Island, Q556632 (as places.json)
    "mossvalley": (-34.55, 150.3833),               # 22.05. Moss Vale NSW, Q3324945
    "thehuntingcampatveimaori": (-9.05, 147.017),   # 19.06. Veimauri River, Q16902588
    "huntingcampatveimaori": (-9.05, 147.017),      # 20.06. Veimauri River, Q16902588
    "kosu": (35.1814, 136.9064),                    # 15.08. Nagoya, Q11751
    "miyanoshitatokyoyokohama": (35.4503, 139.6342),  # 17.08. Miyanoshita – Tokyo – Yokohama: end of day, Yokohama Q38283
    "blackmountain": (49.4792, -119.598),           # 13.09. Shingle Creek BC, Q7497459
    "priestslanding": (50.2333, -119.35),           # 16.09. Okanagan Landing (Vernon BC), Q14874735
    "northport": (48.9144, -117.782),               # 18.09. Northport, Washington, Q1504833
}


def norm(s):
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", s or "").lower())


def site_place(s):
    """'Kandy to Kalawewa, Ceylon' → 'Kalawewa'; 'Port Kennedy, Thursday Island (…)' → 'Port Kennedy'."""
    s = re.sub(r"\(.*?\)", "", s or "")
    s = s.split(";")[-1].split(",")[0]
    return re.split(r"\s+to\s+|\s+–\s+", s)[-1].strip()


def at_sea(s):
    return bool(re.search(r"\b(at sea|in see|red sea|ocean|gulf of|reef|near )", s or "", re.I))


def first(v):
    """Kulturpool gives dates as lists."""
    return v[0] if isinstance(v, list) and v else v or None


def trim(s, n=360):
    s = re.sub(r"\s+", " ", html.unescape(s or "").replace("\u00ad", "")).strip()   # ANNO snippets carry &ouml;, &shy;
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def main():
    diary = json.loads((PROTO / "ke_diary.json").read_text(encoding="utf-8"))
    ked = {d["date"]: d for d in diary}
    days_in = json.loads(DAYS.read_text(encoding="utf-8"))["days"]
    enr = load("enrichment.json")
    episodes = enr["episodes"]

    # --- coordinates ----------------------------------------------------------------------
    by_hunt = {}
    for p in load("places_resolved.json"):
        if p.get("lat") is not None:
            for name in [p["label"].split(" (")[0], *p["diary"]]:
                by_hunt.setdefault(norm(name), (p["lat"], p["lon"]))
    by_site = {}
    for d in days_in:
        k = ked.get(d["date"])
        if k and k["lat"] is not None and d["entry_date"] == d["date"]:
            by_site.setdefault(site_place(d["place_site"]), (k["lat"], k["lon"]))
    by_route = {}
    for p in load("route_places.json")["places"]:
        if p.get("lat") is not None:
            for name in (p["label"].split(",")[0].split(" (")[0], p.get("wikidata_label")):
                if name:
                    by_route.setdefault(norm(name), (p["lat"], p["lon"]))

    def locate(d):
        name = site_place(d["place_site"])
        hunt = next((by_hunt[norm(w)] for w in [name, *re.findall(r"\w{4,}", name)] if norm(w) in by_hunt), None)
        if hunt and not at_sea(d["place_site"]):
            return *hunt, "hunt"
        k = ked.get(d["date"])
        if k and k["lat"] is not None and d["entry_date"] == d["date"]:
            return k["lat"], k["lon"], "heading"
        if at_sea(d["place_site"]):
            return None, None, "sea"
        if name in by_site:
            return *by_site[name], "site"
        if norm(name) in by_route:
            return *by_route[norm(name)], "wikidata"
        if norm(name) in HAND:
            return *HAND[norm(name)], "hand"
        return None, None, "none"

    # --- per-day material -----------------------------------------------------------------
    hunt_days = {h["date"]: h for h in load("hunt_entries.json")}
    episode_of = {}
    for ep in episodes:
        for e in ep["diary"]["entries"]:
            episode_of[e["date"]] = ep["id"]

    # All people of the voyage (people.json ← normalization/json/personen_reise.json ← personen.json), also
    # those the diary does not name (most of the crew): they come from the vault and the Ranglisten.
    people = load("people.json")["people"]
    people_out, people_by_day = {}, {}
    for p in people:
        dd = p.get("diary") or {}
        gnd = p.get("gnd") or {}
        linked = gnd.get("status") in ("vault", "lobid", "fixed")
        anno = p.get("anno") or {}
        kp = p.get("kulturpool") or {}
        people_out[p["id"]] = {
            "name": p["name"], "group": p["group"], "role": p.get("role"), "ranks": p.get("ranks") or [],
            "vault_note": p.get("vault_note"), "possible_duplicate": p.get("possible_duplicate"),
            "life": p.get("life_vault") or (" – ".join(x[:4] for x in (gnd.get("born"), gnd.get("died")) if x) if linked else None),
            "professions": gnd.get("professions") if linked else None,
            "gnd": gnd.get("url") if linked else None, "gnd_status": gnd.get("status"), "gnd_note": gnd.get("note"),
            "wikidata": p.get("wikidata"), "wikidata_description": p.get("wikidata_description"),
            "days": dd.get("days", 0), "first": dd.get("first"), "last": dd.get("last"), "dates": dd.get("dates", []),
            "kill_sentences": dd.get("kill_sentences", 0), "hunts": dd.get("hunts", []),
            "kill_quotes": [{"date": q["date"], "text": trim(q["text"], 360)} for q in dd.get("kill_quotes", [])],
            "anno_total": anno.get("total"),
            "anno": [{"title": x["title"], "date": x["date"], "url": x["url"], "snippet": trim(x.get("snippet"), 260)}
                     for x in anno.get("examples", [])],
            "kulturpool_found": kp.get("found", 0),
            "kulturpool": [{"title": trim(x["title"], 160), "url": x["url"], "provider": x.get("provider"), "date": first(x.get("date"))}
                           for x in kp.get("items", [])[:3]],
        }
        for date in dd.get("dates", []):
            people_by_day.setdefault(date, []).append(p["id"])

    photos = []
    for r in load("europeana.json")["records"]:
        photos.append({
            "title": r["title"], "date": r.get("date"), "place": r.get("day_place"),
            "creator": ", ".join(re.sub(r"\s+Fotograf/in$", "", c) for c in r["creators"]),
            "rights": r["rights"], "open": "creativecommons" in r["rights"],
            "preview": r.get("preview"), "url": r.get("is_shown_at") or r["europeana"],
            "europeana": r["europeana"], "vf": r.get("vf"), "hunt": r.get("hunt"),
        })
    photos_by_day = {}
    for i, ph in enumerate(photos):
        if ph["date"]:
            photos_by_day.setdefault(ph["date"], []).append(i)

    objects = []
    for o in load("objects.json")["objects"]:
        if o["strength"] not in ("strong", "medium"):
            continue
        ev = next((x for x in o["diary"] if x.get("acquisition")), o["diary"][0] if o["diary"] else None)
        st = o["stay"][0] if o["stay"] else {}
        objects.append({
            "inventory": o["inventory"], "type": o["type"],
            "title": None if o["title"] in ("NA", o["type"].upper()) else o["title"],
            "region": st.get("region"), "strength": o["strength"], "url": o["url"],
            "date": ev["date"] if ev else st.get("first"),
            "evidence": trim(ev["text"]) if ev else None,
            "page_url": ev["page_url"] if ev else None,
            "acquisition": bool(ev and ev.get("acquisition")),
            "card": "; ".join(c["text"] for c in o["card"]) or None,
        })
    objects_by_day = {}
    for i, o in enumerate(objects):
        if o["date"]:
            objects_by_day.setdefault(o["date"], []).append(i)

    heroes = load("heroes.json")
    heroes_by_day = {}
    for h in heroes["heroes"]:
        for r in h["route"]:
            if r.get("date"):
                heroes_by_day.setdefault(r["date"], []).append({"id": h["id"], "event": r["event"]})

    # press: automatic ANNO hits (high) from the episodes + rows entered by hand in presse_anno.csv
    press_auto = []
    for ep in episodes:
        for a in ep["anno"]["articles"]:
            press_auto.append({
                "episode": ep["id"], "date": a["date"], "relevance": a["relevance"],
                "newspaper": re.sub(r"\s+\d{1,2}\.\s+\S+\s+\d{4}$", "", a["title"]),
                "place": a.get("pub_place"), "url": a["url"],
                "snippets": [{"text": trim(s["text"], 420), "url": s["url"], "page": s.get("page")} for s in a["snippets"][:2]],
            })
    press_manual = []
    ked_bundle = (PROTO / "ke_diary.js").read_text(encoding="utf-8")
    for p in json.loads(ked_bundle[ked_bundle.index("=") + 1:].strip().rstrip(";")).get("presse", []):
        if not (p.get("added_by") or "").startswith(AUTO):
            press_manual.append({k: p.get(k) for k in ("date", "newspaper", "page_url", "place", "quote", "voice", "added_by")})

    days = []
    for d in days_in:
        lat, lon, how = locate(d)
        h = hunt_days.get(d["date"])
        k = ked.get(d["entry_date"]) or {}
        days.append({
            "date": d["date"], "place": d["place_site"], "heading": d["heading_ocr"] or k.get("heading") or "",
            "entry": d["entry_date"], "method": d["method"], "days_in_entry": d.get("days_in_entry"),
            "band": d.get("band"), "scan": d.get("scan"), "page_url": d.get("page_url"), "site_url": d.get("site_url"),
            "lat": lat, "lon": lon, "coords": how,
            "hunt": {
                "n": h["kill_sentences"], "first_person": h.get("first_person", 0), "animals": h["animals"],
                "quotes": [{"text": trim(q["text"], 420), "first_person": q.get("first_person")} for q in h["quotes"][:4]],
            } if h and h["kill_sentences"] else None,
            "episode": episode_of.get(d["date"]),
            "people": people_by_day.get(d["date"], []),
            "photos": photos_by_day.get(d["date"], []),
            "objects": objects_by_day.get(d["date"], []),
            "heroes": heroes_by_day.get(d["date"], []),
        })

    eps = []
    for ep in episodes:
        eps.append({
            "id": ep["id"], "start": ep["start"], "end": ep["end"],
            "label": " · ".join(p["label"] for p in ep["places"]),
            "places": [{k: p.get(k) for k in ("label", "lat", "lon", "wikidata", "coord_note", "on_route")} for p in ep["places"]],
            "animals": ep["animals"], "kill_sentences": ep["diary"]["kill_sentences"],
            "quotes": [{"text": trim(q["text"], 420), "date": q["date"], "first_person": q.get("first_person"),
                        "band": q.get("band"), "scan": q.get("scan")} for q in ep["diary"]["quotes"][:8]],
            "anno": {"window": ep["anno"]["window"], "issues_found": ep["anno"]["issues_found"],
                     "issues_high": ep["anno"]["issues_high"]},
            "hoefer": ep["hoefer"],
            "photos_hoefer": [{k: p.get(k) for k in ("source", "title", "date", "url", "vf_id", "image", "rights")} for p in ep["photos"]],
            "people": [{k: p.get(k) for k in ("id", "name", "group", "kill_sentences")} for p in ep["people"]],
            "kulturpool": [{k: r.get(k) for k in ("title", "provider", "url", "image", "rights", "description")} | {"direct": kind == "direct"}
                           for kind in ("direct", "context") for r in ep["kulturpool"][kind]],
        })

    voyage = enr["voyage"]
    bundle = {
        "built_by": "enrichment/08_export_prototype.py",
        # GeoNames places of ke_diary.json with today's coordinates: the keys of prototype/data/ke_places_1872.js
        # (positions on the 1872 map); the page moves every point like the nearest of these places
        "geonames": {d["place"]: [d["lat"], d["lon"]] for d in reversed(diary) if d["place"] and d["lat"] is not None},
        "animals": {a["id"]: a["de"] for a in ANIMALS},
        "days": days, "episodes": eps,
        "press": press_auto, "press_manual": press_manual,
        "photos": photos, "photographers": [{k: p[k] for k in ("id", "name", "role", "kept")} for p in voyage["europeana"]["photographers"]],
        "objects": objects,
        "people": people_out,
        "person_sources": [{
            "name": p["name"], "category": p["category"], "role": p["role"],
            "sources": {s: {"kept": v["kept"], "raw": v["raw"],
                            "items": [{k: it.get(k) for k in ("title", "text", "url", "page_url", "place", "snippet", "newspaper")}
                                      | {"date": first(it.get("date"))} for it in v["items"][:3]]}
                        for s, v in p["sources"].items()},
        } for p in load("person_sources.json")["people"]],
        "heroes": heroes["heroes"], "heroes_people": heroes["people"], "heroes_press": heroes.get("summary_press", []),
        "kulturpool": [{k: r.get(k) for k in ("title", "provider", "url", "image", "rights", "description", "year", "tier")} for r in voyage["kulturpool"]],
        "anno_coverage": voyage["anno_coverage"]["months"],
        "anno_topics": [{"label": t["label"], "start": t["start"], "end": t["end"], "total": t["total"],
                         "documents": [{"title": x["title"], "url": x["url"], "snippet": trim(x["snippets"][0]["text"], 300) if x["snippets"] else ""}
                                       for x in t["documents"][:6]]} for t in voyage["anno_topics"]],
    }
    TARGET.write_text("window.KEE = " + json.dumps(bundle, ensure_ascii=False) + ";\n", encoding="utf-8")
    from collections import Counter
    print(f"{len(days)} days, coords {dict(Counter(d['coords'] for d in days))}")
    print(f"{len(eps)} episodes, {len(press_auto)} ANNO articles + {len(press_manual)} by hand, {len(photos)} photos, "
          f"{len(objects)} objects, {len(people_out)} people, {len(heroes['heroes'])} animals")
    print(f"wrote {TARGET.relative_to(ROOT.parent)} ({TARGET.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
