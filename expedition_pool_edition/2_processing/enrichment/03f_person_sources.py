"""Step 3f: selected people of the voyage in all our sources, filtered by the journey's dates and places.

People (curated list from the team): the hunter Janaczek, captain Becker, the photographers Ahrlé, Hodek,
Ramberg, Reményi, Lala Deen Dayal (Hyderabad), the ship's doctors Bém and Plumert.

Sources: diary by day (normalization), Weltmuseum TMS exports (bilder.json, objekte.json), ANNO, Kulturpool,
Europeana (key from .env), Wikimedia Commons, GND/Wikidata (from data/people.json).

Common names need precise queries (Becker, Bém: rank or ship next to the name). A hit is kept only if it
names the person together with their role or the voyage's context (per-person "ctx": Leibjäger, Linienschiffsarzt,
Fähnrich, Elisabeth ...; regiment names and adverts excluded), and belongs to the journey:
  voyage     dated 15.12.1892 - 31.10.1893
  reception  press up to 31.12.1894 (reports, trophies, exhibition)
  undated    no date, but the text names the voyage, Franz Ferdinand, the ship or a stop of the route
  modern     a record of our time about the voyage (e.g. the 2010 exhibition)
  ff_collection  Weltmuseum photo with a VF number (Franz Ferdinand's collection), undated and without a voyage term
Raw and kept counts are reported per source, so the filter can be judged.

Output: data/person_sources.json
"""
import html
import json
import re
import unicodedata

from common import ROOT, env, get_json, load, save

NORM = ROOT.parent / "normalization" / "json"
ANNO = "https://anno.onb.ac.at/anno-suche/rest/search"
KP = "https://api.kulturpool.at/v2/search"
EU = "https://api.europeana.eu/record/v2/search.json"
COMMONS = "https://commons.wikimedia.org/w/api.php"
VOYAGE = ("1892-12-15", "1893-10-31")
RECEPTION_END = "1894-12-31"
PERSONS = [
    {"id": "janaczek", "ctx": r"Leibj[äa]ger|Erzherzog|Thronfolger|Franz Ferdinand|Konopi", "name": "Janaczek, Franz", "category": "Jäger", "role": "Leibjäger Franz Ferdinands",
     "rx": r"Jana[cč]z?ek|Janatschek", "anno": '"Janaczek" OR "Janatschek"', "kp": "Janaczek",
     "eu": '"Janaczek" OR "Janatschek"', "commons": "Janaczek"},
    {"id": "becker", "ctx": r"Elisabeth|Linienschiff|Commandant|Capit[äa]n|Marine|Erzherzog|Contre", "name": "Becker, Alois Ritter von", "category": "Kapitän", "role": "Kommandant der Kaiserin Elisabeth",
     "rx": r"Alois\W{1,3}(Ritter\W+von\W+)?Becker|Becker,?\W+Alois|(Capit[äa]n|Commandant|Linienschiffs-?\s?Capit[äa]n|Contre-?[Aa]dmiral)\W+(von\W+)?Becker",
     "anno": '"Capitän Becker"~3 OR "Commandant Becker"~3 OR "Linienschiffs-Capitän Becker"~3 OR "Alois Becker"~3 OR "Becker Kaiserin Elisabeth"~25',
     "kp": "Alois Becker", "eu": '"Alois Becker" OR "Becker, Alois" OR "Alois von Becker"', "commons": '"Alois von Becker"'},
    {"id": "ahrle", "ctx": r"Photograph|Fotograf|India|Indien|Franz Ferdinand|Erzherzog|Archduke", "name": "Ahrlé, Frederick", "category": "Fotograf", "role": "Fotograf in Nordwest-Indien",
     "rx": r"Ahrl[eé]", "anno": "Ahrlé OR Ahrle", "kp": "Ahrle", "eu": "Ahrle OR Ahrlé", "commons": "Ahrle"},
    {"id": "hodek", "ctx": r"Weltreise|Erzherzog|Archduke|Franz Ferdinand|Thronfolger|Elisabeth|Pr[äa]parator|Photograph|Fotograf", "name": "Hodek, Eduard", "category": "Fotograf", "role": "Fotograf und Präparator an Bord (Eduard Hodek jun.)",
     "rx": r"Hodek", "anno": '"Hodek" AND (Erzherzog OR Thronfolger OR Weltreise OR "Kaiserin Elisabeth" OR Präparator)',
     "kp": "Hodek", "eu": 'who:"Hodek" OR ("Hodek" AND ("Franz Ferdinand" OR Weltreise))', "commons": "Hodek Franz Ferdinand"},
    {"id": "ramberg", "ctx": r"August|Linienschiff|F[äa]hnrich|Seecadet|Elisabeth|Marine|Erzherzog", "name": "Ramberg, August Freiherr von", "category": "Fotograf", "role": "Seeoffizier, Fotograf, Marinemaler",
     "rx": r"Ramberg", "anno": '"Ramberg" AND (Linienschiffs* OR Seecadet* OR Marine OR "Kaiserin Elisabeth" OR Erzherzog)',
     "kp": "Ramberg", "eu": '"August von Ramberg" OR "Ramberg, August" OR "August Ramberg"', "commons": '"August von Ramberg"'},
    {"id": "remenyi", "ctx": r"Franz\W+Rem|Linienschiff|F[äa]hnrich|Seecadet|Elisabeth|Marine", "name": "Reményi, Franz", "category": "Fotograf", "role": "laut Vault Fotograf, Marinemaler (Notiz gleicht der von Ramberg)",
     "rx": r"Rem[eé]nyi", "anno": '"Reményi" AND (Linienschiffs* OR Seecadet* OR Marine OR "Kaiserin Elisabeth" OR Fähnrich)',
     "kp": "Reményi", "eu": '"Franz Reményi" OR "Ferenc Reményi" OR "Franz Remenyi"', "commons": '"Franz Reményi"'},
    {"id": "bem", "ctx": r"Linienschiff|Schiffsarzt|Marine|Elisabeth|Pola", "name": "Bém, Jaroslaw, Dr.", "category": "Arzt", "role": "Linienschiffsarzt",
     "rx": r"(Dr\.?|Doctor|Linienschiffs-?\s?[Aa]rzt|Jaroslaw?|Jaroslav)\W{1,3}B[eé]m\b|B[eé]m,?\W+Jaroslaw?",
     "anno": '("Dr. Bém"~1 OR "Dr. Bem"~1 OR "Linienschiffsarzt Bém"~2 OR "Jaroslaw Bém"~2) AND (Marine OR "Kaiserin Elisabeth" OR Linienschiffsarzt OR Pola)',
     "kp": "Jaroslav Bém", "eu": '"Jaroslav Bém" OR "Jaroslaw Bém"', "commons": '"Jaroslav Bém"'},
    {"id": "deen-dayal", "ctx": r"Hyderabad|Haidarabad|Secunderabad|Nizam|Franz Ferdinand|Erzherzog|Archduke|Photograph|Fotograf",
     "strict": True, "name": "Dayal, Lala Deen", "category": "Fotograf", "role": "Hoffotograf des Nizam in Hyderabad",
     "rx": r"(Deen|Din)\W?Dayal|Dindayal", "anno": '"Deen Dayal" OR "Din Dayal" OR "Dindayal"', "kp": "Deen Dayal",
     "eu": '"Deen Dayal" OR "Din Dayal" OR "Dindayal"', "commons": '"Deen Dayal" Franz Ferdinand'},
    {"id": "plumert", "ctx": r"Linienschiff|Schiffsarzt|Marine|Elisabeth|Pola|Arthur|Arturo", "name": "Plumert, Arthur, Dr.", "category": "Arzt", "role": "Linienschiffsarzt",
     "rx": r"Plumert", "anno": '"Plumert"', "kp": "Plumert", "eu": "Plumert", "commons": '"Arthur Plumert"'},
]
NOT_PERSON = re.compile(r"Regiment|Uhlanen|Infanterie|Lebensbalsam", re.I)   # "Freiherr von Ramberg Nr. 96", adverts
JOURNEY = re.compile(r"Franz.?Ferdinand|Erzherzog|Archduke|Thronfolger|Weltreise|Kaiserin Elisabeth|Empress Elisabeth|"
                     r"Reise um die Erde", re.I)


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", html.unescape(s or "")) if not unicodedata.combining(c))


def flat(v):
    if isinstance(v, list):
        return " ".join(flat(x) for x in v)
    if isinstance(v, dict):
        return " ".join(flat(x) for x in v.values())
    return str(v or "")


def stops_rx():
    names = set()
    for p in load("route_places.json")["places"]:
        names.add(re.split(r"[,(]", p["label"])[0].strip())
    for p in load("places_resolved.json"):
        names |= {v for v in p["diary"] + p["anno"] if len(v) > 3}
    names |= {"Ceylon", "Indien", "India", "Nepal", "Java", "Sydney", "Neu-Guinea", "New Guinea", "Japan", "Hongkong", "Singapur"}
    return re.compile(r"\b(" + "|".join(sorted(map(re.escape, names), key=len, reverse=True)) + r")\b", re.I)


STOPS = None


def years(text):
    return [int(y) for y in re.findall(r"\b(1[89]\d\d)\b", text or "")]


def journey_kind(date, text, strict=False):
    """voyage / reception by date, else undated with a journey mention; None = not this journey.
    strict: a stop of the route alone is not enough (for people who lived at a stop, e.g. Deen Dayal in Hyderabad)."""
    if date:
        if VOYAGE[0] <= date <= VOYAGE[1]:
            return "voyage"
        if VOYAGE[1] < date <= RECEPTION_END or "1892-11-01" <= date < VOYAGE[0]:
            return "reception"
        return None
    ys = years(text)
    if ys and not any(1892 <= y <= 1894 for y in ys) and not JOURNEY.search(text):
        return None
    if JOURNEY.search(text) or (not strict and STOPS.search(text)):
        return "undated" if not ys else ("voyage" if any(y in (1892, 1893) for y in ys) else "reception")
    return None


def is_person(p, text):
    """The text names this person (name pattern) in their role or the voyage's context, not a namesake."""
    t = fold(text)
    return bool(re.search(p["rx"], t, re.I) and re.search(p["ctx"], t, re.I) and not NOT_PERSON.search(t[:400]))


def diary(p):
    days = json.loads((NORM / "tagebuch_tage.json").read_text())["days"]
    rx = re.compile(p["rx"] if p["id"] not in ("becker", "bem") else {"becker": r"\bBecker\b", "bem": r"\bB[eé]m\b"}[p["id"]])
    hits = [{"date": d["date"], "place": d["place_site"], "scan": d["scan"], "page_url": d["page_url"], "text": s[:300]}
            for d in days if d["text"] for s in re.split(r"(?<=[.!?;])\s+", d["text"]) if rx.search(s)]
    return {"raw": len(hits), "kept": len(hits), "items": hits}


def tms(p):
    rx = re.compile(p["rx"], re.I)
    items, raw = [], 0
    for fname, kind in (("bilder.json", "photo"), ("objekte.json", "object")):
        for o in json.loads((NORM / fname).read_text()):
            text = " ".join(flat(o.get(f)) for f in ("Titel", "Bildbeschreibung", "Beschreibung", "Transkription"))
            if rx.search(fold(text)) or rx.search(text):
                raw += 1
                items.append({"kind": kind, "inventory": flat(o["Inventarnummer"]), "title": o["Titel"],
                              "dating": o.get("Datierung"), "url": flat(o.get("Weltmuseum-Link"))})
    return {"raw": raw, "kept": len(items), "items": items}


def anno(p):
    d = get_json(f"{ANNO}/complex", {"text": p["anno"], "dateFrom": "1892-11-01", "dateTo": RECEPTION_END, "from": 1})
    total, docs = d.get("totalHits", 0), d.get("documents", [])
    for page in (11, 21):
        if len(docs) < total:
            docs += get_json(f"{ANNO}/complex", {"text": p["anno"], "dateFrom": "1892-11-01", "dateTo": RECEPTION_END,
                                                 "from": page}).get("documents", [])
    rx = re.compile(p["rx"], re.I)
    term = re.findall(r"[A-ZÄÖÜ][a-zäöüé]+", p["name"])[0]
    items = []
    for doc in docs[:30]:
        date = doc["uid"].get("annoDate", {}).get("date")
        s = get_json(f"{ANNO}/snippet", {"documentId": doc["docId"], "query": term})
        snips = [re.sub(r"\s+", " ", fold(re.sub(r"<[^>]+>", "", x["text"]))) for pg in s.get("snippetPages", [])
                 for x in pg["snippets"]]
        good = [t for t in snips if is_person(p, t)]
        kind = journey_kind(date, " ".join(good), p.get("strict", False))
        if good and kind:
            items.append({"date": date, "title": doc["displayTitle"], "url": doc["openUrl"], "kind": kind, "snippet": good[0][:300]})
    return {"raw": total, "checked": min(len(docs), 30), "kept": len(items), "items": items}


def kulturpool(p):
    d = get_json(KP, {"q": p["kp"], "per_page": 100})
    rx = re.compile(p["rx"], re.I)
    items = []
    for h in d.get("hits", []):
        x = h["document"]
        text = " ".join([x.get("title") or ""] + (x.get("description") or []) + (x.get("creator") or []) + (x.get("subject") or []))
        if not is_person(p, text):
            continue
        own = [int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", " ".join(x.get("date") or []))]
        kind = "modern" if own and min(own) >= 1990 else \
            journey_kind(None, text + " " + " ".join(x.get("date") or []) + " " + " ".join(x.get("spatial") or []), p.get("strict", False))
        if kind:
            items.append({"title": x.get("title"), "provider": x.get("dataProvider"), "date": x.get("date"),
                          "url": x.get("url"), "kind": kind})
    return {"raw": d.get("found", 0), "kept": len(items), "items": items}


def europeana(p, key):
    items, raw, cursor, seen = [], 0, "*", 0
    rx = re.compile(p["rx"], re.I)
    while cursor and seen < 600:
        d = get_json(EU, {"wskey": key, "query": p["eu"], "rows": 100, "profile": "rich", "cursor": cursor})
        raw = d.get("totalResults", 0)
        for it in d.get("items", []):
            text = " ".join(flat(it.get(f)) for f in ("title", "dcDescription", "dcCreator", "edmAgentLabel", "dcSubjectLangAware"))
            if not is_person(p, text):
                continue
            kind = journey_kind(None, text + " " + flat(it.get("year")), p.get("strict", False))
            if not kind and re.search(r"/15504/VF_", it["id"]):   # Weltmuseum VF photo = Franz Ferdinand's collection (as in 03e)
                kind = "ff_collection"
            if kind:
                items.append({"title": flat(it.get("title"))[:200], "provider": flat(it.get("dataProvider")),
                              "rights": flat(it.get("rights")), "url": f"https://www.europeana.eu/item{it['id']}",
                              "type": it.get("type"), "kind": kind})
        seen += len(d.get("items", []))
        cursor = d.get("nextCursor")
    return {"raw": raw, "checked": seen, "kept": len(items), "items": items}


def commons(p):
    r = get_json(COMMONS, {"action": "query", "list": "search", "srsearch": p["commons"], "srnamespace": 6,
                           "srlimit": 50, "format": "json"})
    if "query" not in r:   # API error (e.g. rate limit): report it, don't pretend there were no hits
        return {"raw": None, "kept": 0, "items": [], "error": (r.get("error") or {}).get("info", "no result")}
    rx = re.compile(p["rx"], re.I)
    items = []
    for x in r["query"]["search"]:
        text = fold(re.sub(r"<[^>]+>", "", x["title"] + " " + x.get("snippet", "")))
        if is_person(p, text) and (kind := journey_kind(None, text, p.get("strict", False))):
            items.append({"title": x["title"], "url": "https://commons.wikimedia.org/wiki/" + x["title"].replace(" ", "_"),
                          "kind": kind})
    return {"raw": r["query"]["searchinfo"]["totalhits"], "kept": len(items), "items": items}


def main():
    global STOPS
    STOPS = stops_rx()
    key = env("EUROPEANA_API_KEY")
    people = {x["name"]: x for x in load("people.json")["people"]}
    out = []
    for p in PERSONS:
        pp = people.get(p["name"], {})
        res = {"diary": diary(p), "weltmuseum_tms": tms(p), "anno": anno(p), "kulturpool": kulturpool(p),
               "europeana": europeana(p, key), "commons": commons(p)}
        gnd = pp.get("gnd") or {}
        out.append({k: p[k] for k in ("id", "name", "category", "role")} | {
            "vault_id": pp.get("id"), "gnd": gnd.get("url"), "gnd_status": gnd.get("status"), "wikidata": pp.get("wikidata"),
            "sources": res})
        print(f"  {p['name'][:28]:<28} " + "  ".join(f"{s}:{r['raw']}->{r['kept']}" for s, r in res.items()))
    save("person_sources.json", {
        "about": "Selected people in all sources; raw = hits of the query, kept = names the person and belongs to "
                 f"the journey (voyage {VOYAGE[0]}..{VOYAGE[1]}, reception to {RECEPTION_END}, or undated with a "
                 "journey/route mention). Common names searched with rank or ship next to the name.",
        "people": out})


if __name__ == "__main__":
    main()
