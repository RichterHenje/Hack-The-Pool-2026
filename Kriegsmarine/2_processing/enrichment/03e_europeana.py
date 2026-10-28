"""Step 3e: photographs of the voyage in the Europeana network, by the photographers who were there.

Europeana Search API (https://api.europeana.eu/record/v2/search.json), key EUROPEANA_API_KEY from the
environment or the repo's .env (not written anywhere). Per photographer: who:"<name>" queries for
images, kept if the creator field names the photographer (namesakes like the Czech graphic artist
Josef Hodek are dropped) and the record belongs to the voyage: Weltmuseum Wien photo (VF number, the
FF collection) or a voyage date/place/term in title or description. Creators given only as GND URIs
are resolved via lobid-gnd.

Per record: title, creator, data provider, licence (edm:rights), Europeana page, preview, VF number
(-> normalization/json/bilder.json), date parsed from the title ("24.II.1893") -> diary day and
hunting episode, animals named (German/English).

Output: data/europeana.json
"""
import json
import re

from common import ROOT, env, get_json, load, save

API = "https://api.europeana.eu/record/v2/search.json"
LOBID = "https://lobid.org/gnd/"
NORM = ROOT.parent / "normalization" / "json"
PHOTOGRAPHERS = [
    {"id": "hodek", "name": "Eduard Hodek jun.", "role": "Fotograf und Präparator an Bord",
     "queries": ['who:"Hodek"', '"Hodek" AND ("Franz Ferdinand" OR Erzherzog OR Archduke)'],
     "creator": r"Eduard.?Hodek|Hodek jun|Hodek junior|Hodeks?\b.*(Franz Ferdinand|Erzherzog|Archduke)"},
    {"id": "deen-dayal", "name": "Lala Deen Dayal", "role": "Hoffotograf in Hyderabad",
     "queries": ['who:"Deen Dayal"', '"Deen Dayal" AND ("Franz Ferdinand" OR Erzherzog OR Archduke)'],
     "creator": r"Deen Dayal|Din Dayal"},
    {"id": "pietzner", "name": "Carl Pietzner", "role": "Wiener Hofatelier, Abzüge der Reisefotos",
     "queries": ['who:"Pietzner" AND ("Franz Ferdinand" OR Erzherzog OR Indien OR Japan OR Ceylon OR Nepal OR Java OR Siriska)'],
     "creator": r"Pietzner"},
    {"id": "bourne-shepherd", "name": "Bourne & Shepherd", "role": "Fotostudio in Indien",
     "queries": ['who:"Bourne & Shepherd" AND ("Franz Ferdinand" OR Archduke OR 1893)'], "creator": r"Bourne"},
    {"id": "imhof", "name": "Max von Imhof", "role": "Fotograf in Nordamerika",
     "queries": ['who:"Imhof" AND ("Franz Ferdinand" OR Erzherzog OR 1893)'], "creator": r"Imhof"},
]
# outside the Weltmuseum's VF photos (FF collection) a record must name FF, the voyage or the ship, or a
# stop of the route together with a voyage date; "Erzherzog"/"Archduke" alone also matches other
# archdukes (a WWI postcard of Franz Salvator), a place alone other photos (Deen Dayal's Hyderabad buildings)
VOYAGE = re.compile(r"Franz.Ferdinand|Ferenc Ferdin|Weltreise|Kaiserin Elisabeth|Empress Elisabeth", re.I)
STOP = re.compile(r"Siriska|Tandur|Hyderabad|Haidarabad|Secunderabad|Nikko|Nicco|Kalawewa|Katni|Ulwar|Alwar|Ceylon|"
                  r"Nepal|Jeypore|Jaipur|Java|Sydney|Neu-?Guinea|New Guinea|Japan", re.I)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12}
EN_ANIMALS = {"tiger": r"\btigers?\b", "elephant": r"\belephants?\b", "leopard": r"\bleopards?\b|\bpanthers?\b",
              "crocodile": r"\bcrocodiles?\b", "buffalo": r"\bbuffalo", "deer": r"\bdeer\b|\bstag", "kangaroo": r"kangaroo",
              "bear": r"\bbears?\b", "boar": r"\bboars?\b|pig.?sticking", "bird": r"\bbirds?\b|\bparrots?\b|\bcockatoo",
              "monkey": r"\bmonkeys?\b|\bapes?\b", "cheetah": r"\bcheetahs?\b|\bGepard"}
TEXT_FIELDS = ("title", "dcDescription", "dcCreator", "edmAgentLabel")


def flat(v):
    if isinstance(v, list):
        return " ".join(flat(x) for x in v)
    if isinstance(v, dict):
        return " ".join(flat(x) for x in v.values())
    return str(v or "")


def gnd_name(uri, cache={}):
    m = re.search(r"d-nb\.info/(?:gnd/)?(\w+)", uri)
    if not m:
        return None
    if m.group(1) not in cache:
        try:
            cache[m.group(1)] = get_json(f"{LOBID}{m.group(1)}.json").get("preferredName")
        except Exception:
            cache[m.group(1)] = None
    return cache[m.group(1)]


def creators(it):
    out = []
    for c in (it.get("dcCreator") or []) + [a for a in (it.get("edmAgentLabel") or []) if isinstance(a, str)]:
        c = str(c)
        out.append(gnd_name(c) or c if c.startswith("http") else c.lstrip("#").replace("_", " "))
    return list(dict.fromkeys(x for x in out if x))


def date_of(text):
    if m := re.search(r"\b(\d{1,2})\.\s*([IVX]{1,4})\.\s*(189[23])", text):
        if m.group(2) in ROMAN:
            return f"{m.group(3)}-{ROMAN[m.group(2)]:02d}-{int(m.group(1)):02d}"
    if m := re.search(r"\b(\d{1,2})\.(\d{1,2})\.(189[23])", text):
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return None


def search(query, key):
    items, cursor = [], "*"
    while cursor and len(items) < 1000:
        d = get_json(API, {"wskey": key, "query": query, "qf": "TYPE:IMAGE", "rows": 100,
                           "profile": "rich", "cursor": cursor})
        items += d.get("items", [])
        cursor = d.get("nextCursor")
    return items


def main():
    key = env("EUROPEANA_API_KEY")
    bilder = {i: b for b in json.loads((NORM / "bilder.json").read_text())
              for i in (b["Inventarnummer"] if isinstance(b["Inventarnummer"], list) else [b["Inventarnummer"]])}
    days = {d["date"]: d for d in json.loads((NORM / "tagebuch_tage.json").read_text())["days"]}
    hunt_of = {d["date"]: h["id"] for h in load("hunts.json") if h["region"] for d in h["diary"]}
    animals = json.loads((ROOT / "animals.json").read_text())
    records, summary = {}, []
    for ph in PHOTOGRAPHERS:
        seen = {}
        for q in ph["queries"]:
            for it in search(q, key):
                seen[it["id"]] = it
        kept = 0
        for it in seen.values():
            cr = creators(it)
            text = " ".join(flat(it.get(f)) for f in TEXT_FIELDS)
            if not re.search(ph["creator"], " ".join(cr) + " " + text, re.I) or not any(re.search(ph["creator"], c, re.I) for c in cr + [text]):
                continue
            vf = re.search(r"/15504/(VF_\w+)$", it["id"])
            if not (vf or VOYAGE.search(text) or (STOP.search(text) and date_of(text))):
                continue
            if not any(re.search(ph["creator"], c, re.I) for c in cr):   # the creator field must name him
                continue
            kept += 1
            date = date_of(text)
            r = records.setdefault(it["id"], {
                "id": it["id"], "title": flat(it.get("title"))[:300], "description": flat(it.get("dcDescription"))[:500],
                "creators": cr, "photographers": [], "provider": (it.get("dataProvider") or [None])[0],
                "rights": (it.get("rights") or [None])[0], "europeana": f"https://www.europeana.eu/item{it['id']}",
                "is_shown_at": (it.get("edmIsShownAt") or [None])[0], "preview": (it.get("edmPreview") or [None])[0],
                "vf": vf.group(1) if vf else None, "in_bilder_json": bool(vf and vf.group(1) in bilder),
                "date": date, "day_place": days.get(date, {}).get("place_site") if date else None,
                "hunt": hunt_of.get(date) if date else None,
                "animals": sorted({a["id"] for a in animals if re.search(a["pattern"], text, re.I)} |
                                  {k for k, rx in EN_ANIMALS.items() if re.search(rx, text, re.I)}),
            })
            r["photographers"].append(ph["id"])
        summary.append({"id": ph["id"], "name": ph["name"], "role": ph["role"], "queries": ph["queries"],
                        "searched": len(seen), "kept": kept})
        print(f"  {ph['name']:<20} searched {len(seen):>4}  kept {kept:>4}")
    recs = sorted(records.values(), key=lambda r: (r["date"] or "9999", r["title"]))
    rights, providers = {}, {}
    for r in recs:
        rights[r["rights"]] = rights.get(r["rights"], 0) + 1
        providers[r["provider"]] = providers.get(r["provider"], 0) + 1
    save("europeana.json", {
        "source": "Europeana Search API (record/v2), images only; key from .env, not stored",
        "photographers": summary, "rights": rights, "providers": providers,
        "dated": sum(bool(r["date"]) for r in recs), "at_hunts": sum(bool(r["hunt"]) for r in recs),
        "records": recs})
    print(f"{len(recs)} records; dated {sum(bool(r['date']) for r in recs)}, at a hunting episode "
          f"{sum(bool(r['hunt']) for r in recs)}, VF in bilder.json {sum(r['in_bilder_json'] for r in recs)}, "
          f"with animals {sum(bool(r['animals']) for r in recs)}")
    print("  providers", providers)
    print("  rights   ", rights)


if __name__ == "__main__":
    main()
