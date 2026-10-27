"""Step 3c: the people of the voyage – diary presence, hunts, GND/Wikidata, press, Kulturpool.

Input: ../normalization/json/personen_reise.json (people_voyage.py: crew from the vault and the
Ranglisten 1892/93, companions and hosts named in the diary, all in the structure of personen.json).

Per person
  diary      days the diary names the person (normalization/json/tagebuch_tage.json) and kill
             sentences naming them (data/hunt_entries.json) – who was there when FF hunted
  gnd        GND from the vault if present, else lobid-gnd search; accepted only if surname and
             first name match and the record has life dates that fit 1892/93 (and the vault's, if any);
             several fitting candidates = "ambiguous", undated namesakes = "undated"; neither is linked
  wikidata   from the GND record (sameAs)
  anno       newspaper issues Dec 1892 – Dec 1893 naming the person with the archduke (companions,
             hosts, scientists, officers named in the diary)
  kulturpool objects naming the person (only people with an accepted GND)

Output: data/people.json
"""
import json
import re
import unicodedata

from common import ROOT, get_json, load, save

PEOPLE = ROOT.parent / "normalization" / "json" / "personen_reise.json"
DAYS = ROOT.parent / "normalization" / "json" / "tagebuch_tage.json"
LOBID = "https://lobid.org/gnd/search"
ANNO = "https://anno.onb.ac.at/anno-suche/rest/search"
KP = "https://api.kulturpool.at/v2/search"
NA = "NA"
NAVAL = r"marine|offizier|kapitän|kapitan|admiral|soldat|militär|seemann|see"
TITLE = (r"(?:Herr|Herrn|Graf|Grafen|Baron|Freiherr|Capitän|Capitäns|Lieutenant|Linienschiffs-\w+|"
         r"Fregatten-\w+|Corvetten-\w+|Schiffsfähnrich|Dr\.|Major|Mr\.|Captain|Sir|Oberlieutenant|Arzt)\s+")
# surnames that are also German nouns or first names: count only with a title in front
TITLE_ONLY = {"Reiter", "Koch", "Sommer", "Hermann"}
# OCR / name variants in the diary
VARIANTS = {"Prónay": r"Pr[oóö6]nay", "Liburnau": r"Lorenz|Liburnau", "Salvator": r"Leopold Ferdinand",
            "Oscar": r"Henschel"}


# vault name -> (surname, first name) as the GND has it, where the note title is arranged differently
GND_NAME = {"Ritter von Liburnau, Dr. Ludwig Lorenz": ("Lorenz-Liburnau", "Ludwig")}


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s.casefold()) if not unicodedata.combining(c))


def surname(name):
    s = re.split(r",", name)[0]
    s = re.sub(r"^(Ritter von|Salvator von Österreich-Toskana)\s+", "", s)
    return s.split()[0].split("-")[0]


def full_surname(name):
    return re.sub(r"^(Ritter von)\s+", "", name.split(",")[0]).strip()


def forename(p):
    parts = [x.strip() for x in p["Nachname, Vorname"].split(",")[1:]]
    names = [w for x in parts for w in x.split() if w[0].isupper() and not re.match(r"(Ritt|Ritter|Edl|Freih|Freiherr|Graf|Dr|Captain)\b", w)]
    return names[0] if names else None


def pattern(p):
    s = surname(p["Nachname, Vorname"])
    if s in VARIANTS:
        return re.compile(rf"\b(?:{VARIANTS[s]})\b")
    if s in TITLE_ONLY:
        return re.compile(TITLE + re.escape(s) + r"\b")
    return re.compile(rf"\b{re.escape(s)}\b")


def same_forename(a, b):
    """Karl/Carl, Konrad/Conrad: compare folded forenames with a leading C read as K."""
    a, b = fold(a).split()[0] if a.strip() else "", fold(b).split()[0] if b.strip() else ""
    return re.sub(r"^c", "k", a) == re.sub(r"^c", "k", b)


def years(text):
    return [int(y) for y in re.findall(r"\b(1[789]\d\d)\b", text or "")]


def lobid(p):
    """GND candidates whose name and life dates fit; vault GND wins."""
    vault_gnd = [g.rstrip("/").split("/")[-1] for g in (p["GND"] if p["GND"] != NA else [])]
    if vault_gnd:
        r = get_json(LOBID, {"q": f"gndIdentifier:{vault_gnd[0]}", "format": "json"})
        m = (r.get("member") or [None])[0]
        return {"status": "vault", "id": vault_gnd[0], "record": m}
    sur, fn = GND_NAME.get(p["Nachname, Vorname"], (full_surname(p["Nachname, Vorname"]), forename(p)))
    if not fn or p["_meta"]["id"] == NA:
        return {"status": "not_searched"}
    exact = p["Nachname, Vorname"] in GND_NAME          # compare the full (double) surname
    r = get_json(LOBID, {"q": f"{sur if exact else surname(sur)} {fn}", "filter": "type:Person", "format": "json", "size": 10})
    life = years(p.get("Lebensdaten"))
    ok, undated = [], []
    for m in r.get("member", []):
        name = m.get("preferredName", "")
        msur, _, mfn = name.partition(",")
        msur_key, sur_key = (fold(msur.strip()), fold(sur)) if exact else (fold(surname(msur)), fold(surname(sur)))
        if msur_key != sur_key or not same_forename(mfn.strip(), fn):
            continue
        b = years(" ".join(m.get("dateOfBirth", []))) or [None]
        d = years(" ".join(m.get("dateOfDeath", []))) or [None]
        if (b[0] and not 1800 <= b[0] <= 1877) or (d[0] and d[0] < 1893):
            continue
        if not b[0] and not d[0]:          # undated records cannot be told apart from namesakes
            undated.append(m)
            continue
        if life and b[0] and abs(life[0] - b[0]) > 1:
            continue
        ok.append(m)
    if p["_reise"]["gruppe"] == "Besatzung":   # crew: the GND profession must fit the navy (or the ship's doctor)
        context = " ".join([p.get("Beruf/Funktionen") or ""] +
                           [r["dienstgrad"] for x in p["_reise"].get("ranglisten", []) for r in x["ranglisten"]]).lower()
        def fits(m):
            prof = " ".join(x.get("label", "") for x in m.get("professionOrOccupation", [])).lower()
            return bool(re.search(NAVAL, prof)) or ("arzt" in prof and "arzt" in context)
        rejected = [m for m in ok if not fits(m)]
        ok = [m for m in ok if fits(m)]
        if not ok and rejected:
            return {"status": "implausible", "candidates": [{"id": m["gndIdentifier"], "name": m.get("preferredName"),
                    "professions": [x.get("label") for x in m.get("professionOrOccupation", [])][:3]} for m in rejected]}
    if len(ok) == 1:
        return {"status": "lobid", "id": ok[0]["gndIdentifier"], "record": ok[0]}
    if ok:
        return {"status": "ambiguous", "candidates": [{"id": m["gndIdentifier"], "name": m.get("preferredName"),
                                                       "born": m.get("dateOfBirth"), "died": m.get("dateOfDeath")} for m in ok]}
    if undated:
        return {"status": "undated", "candidates": [{"id": m["gndIdentifier"], "name": m.get("preferredName"),
                                                     "professions": [x.get("label") for x in m.get("professionOrOccupation", [])][:3]}
                                                    for m in undated]}
    return {"status": "none"}


def gnd_summary(g):
    m = g.get("record") or {}
    wd = next((s["id"].split("/")[-1] for s in m.get("sameAs", []) if "wikidata.org" in s.get("id", "")), None)
    return {"status": g["status"], "id": g.get("id"), "candidates": g.get("candidates"),
            "name": m.get("preferredName"), "born": (m.get("dateOfBirth") or [None])[0],
            "died": (m.get("dateOfDeath") or [None])[0],
            "professions": [x.get("label") for x in m.get("professionOrOccupation", [])][:5],
            "url": f"https://d-nb.info/gnd/{g['id']}" if g.get("id") else None, "wikidata": wd}


def anno(p):
    s = surname(p["Nachname, Vorname"])
    if s in TITLE_ONLY or s in VARIANTS:
        return None
    q = f'"{s}" AND (Erzherzog OR Thronfolger) AND (Weltreise OR Indien OR Ceylon OR "Kaiserin Elisabeth" OR Japan OR Australien)'
    d = get_json(f"{ANNO}/complex", {"text": q, "dateFrom": "1892-12-01", "dateTo": "1893-12-31", "from": 1})
    docs = d.get("documents", [])[:3]
    out = []
    for doc in docs:
        sn = get_json(f"{ANNO}/snippet", {"documentId": doc["docId"], "query": s})
        texts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x["text"])) for pg in sn.get("snippetPages", []) for x in pg["snippets"]]
        if texts:
            out.append({"title": doc["displayTitle"], "date": doc["uid"].get("annoDate", {}).get("date"),
                        "url": doc["openUrl"], "snippet": texts[0][:300]})
    return {"query": q, "total": d.get("totalHits", 0), "examples": out}


def kulturpool(p, g):
    fn = forename(p)
    if not fn or not g.get("id"):
        return None
    sur = full_surname(p["Nachname, Vorname"])
    hits = get_json(KP, {"q": f"{fn} {sur}", "per_page": 20}).get("hits", [])
    items = []
    for h in hits:
        x = h["document"]
        text = " ".join([x.get("title") or ""] + (x.get("description") or []))
        y = years(" ".join(x.get("date") or [])) or years(x.get("title"))
        if fold(surname(sur)) in fold(text) and (not y or y[0] <= 1930):
            items.append({"title": x.get("title"), "provider": x.get("dataProvider"), "date": x.get("date"),
                          "url": x.get("url"), "image": x.get("previewImage")})
    return {"found": len(items), "items": items[:5]}


def main():
    people = json.loads(PEOPLE.read_text())
    days = [d for d in json.loads(DAYS.read_text())["days"] if d["text"]]
    hunts = load("hunts.json")
    entries = {e["date"]: e for e in load("hunt_entries.json")}
    episode_of = {d["date"]: h["id"] for h in hunts for d in h["diary"]}
    out = []
    for p in people:
        pat = pattern(p)
        mentions = [d["date"] for d in days if pat.search(d["text"])]
        kills = [(date, s) for date, e in entries.items() for s in e["kills"] if pat.search(s)]
        g = lobid(p)
        gs = gnd_summary(g)
        named = len(mentions) >= 3 or p["_reise"]["gruppe"] != "Besatzung"
        out.append({
            "id": p["_meta"]["id"] if p["_meta"]["id"] != NA else f"tagebuch:{p['Nachname, Vorname']}",
            "name": p["Nachname, Vorname"], "group": p["_reise"]["gruppe"], "role": p["_reise"].get("rolle"),
            "ranks": sorted({r["dienstgrad"] for x in p["_reise"].get("ranglisten", []) for r in x["ranglisten"]}),
            "vault_note": p["_meta"]["datei"] if p["_meta"]["datei"] != NA else None,
            "life_vault": p.get("Lebensdaten") if p.get("Lebensdaten") != NA else None,
            "possible_duplicate": p["_reise"].get("moegliche_dublette"),
            "diary": {"pattern": pat.pattern, "days": len(mentions), "first": mentions[0] if mentions else None,
                      "last": mentions[-1] if mentions else None, "dates": mentions,
                      "kill_sentences": len(kills),
                      "hunts": sorted({episode_of[d] for d, _ in kills if d in episode_of}),
                      "kills_by_hunt": {h: sum(1 for d, _ in kills if episode_of.get(d) == h)
                                        for h in sorted({episode_of[d] for d, _ in kills if d in episode_of})},
                      "kill_quotes": [{"date": d, "text": s} for d, s in kills[:3]]},
            "gnd": gs, "wikidata": gs["wikidata"],
            "anno": anno(p) if named else None,
            "kulturpool": kulturpool(p, gs),
        })
    # Wikidata labels/descriptions for linked people
    qids = sorted({x["wikidata"] for x in out if x["wikidata"]})
    if qids:
        r = get_json("https://www.wikidata.org/w/api.php", {"action": "wbgetentities", "ids": "|".join(qids),
                                                            "props": "labels|descriptions", "languages": "de|en", "format": "json"})
        for x in out:
            if (q := x["wikidata"]) and q in r["entities"]:
                e = r["entities"][q]
                x["wikidata_label"] = (e["labels"].get("de") or e["labels"].get("en") or {}).get("value")
                x["wikidata_description"] = (e["descriptions"].get("de") or e["descriptions"].get("en") or {}).get("value")
    out.sort(key=lambda x: (-x["diary"]["days"], x["name"]))
    save("people.json", {"source": "normalization/json/personen_reise.json", "people": out})
    st = {}
    for x in out:
        st[x["gnd"]["status"]] = st.get(x["gnd"]["status"], 0) + 1
    print(f"{len(out)} people; GND: {st}; in diary: {sum(x['diary']['days'] > 0 for x in out)}; "
          f"in kill sentences: {sum(x['diary']['kill_sentences'] > 0 for x in out)}")
    for x in out[:16]:
        print(f"  {x['diary']['days']:>3} days {x['diary']['kill_sentences']:>3} kills  {x['gnd']['status']:<12} "
              f"{x['gnd']['id'] or '':<11} {x['wikidata'] or '':<10} {x['name'][:40]}")


if __name__ == "__main__":
    main()
