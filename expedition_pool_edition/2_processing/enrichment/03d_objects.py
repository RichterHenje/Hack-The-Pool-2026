"""Step 3d: objects of the Este collection (Weltmuseum Wien) and the journey – souvenirs, gifts, trophies.

Input: ../normalization/json/objekte.json (1,798 online objects from the Este inventories, TMS export
by Henje Richter) and the diary by days (normalization/json/tagebuch_tage.json).

For each object we collect evidence that ties it to a day or stop of the voyage:
  place      the object's region (Henje's "Ortschaft (Route)", else "Geografie") -> the diary days at
             that stop (place names of franzferdinandsworld.com in tagebuch_tage.json). "direct" if
             FF was there; "via" for regions he did not visit but whose objects were sold at a stop
             (Tibet/Sikkim/Bhutan -> Darjeeling, Moluccas -> Amboina, Borneo -> Kuching); "India"
             alone is too broad and gets no days.
  diary      on those days, sentences naming the object type (a word of "Objektbezeichnung", inflected
             but not inside a compound);
             "acquisition" if the sentence speaks of buying, gifts, a bazaar or a collection
  card       the museum's index card (transcription): gift to the archduke, occasion, School of Art,
             collection year 1892/93
  animals    animal materials or motifs (animals.json + fur, horn, ivory, feathers ...) and the
             hunting episodes at the same stop
Every link is a suggestion with its evidence; nothing here is checked by the museum.

Output: data/objects.json
"""
import json
import re

from common import ROOT, load, save

NORM = ROOT.parent / "normalization" / "json"
ANIMALS = json.loads((ROOT / "animals.json").read_text())
SKIP_INDIA = {"Indien", "Südasien", "unbestimmt"}
# object region -> (regex on the site's day place, link kind)
REGIONS = [
    (r"^Jaipur$", r"Jaipur", "direct"), (r"^Hyderabad$", r"Hyderabad|Tandur|Sikanderab", "direct"),
    (r"^Delhi$", r"Delhi", "direct"), (r"^Gwalior$", r"Gwalior", "direct"), (r"^Varanasi$", r"Benares", "direct"),
    (r"^Mumbai$", r"Bombay|Poona", "direct"), (r"^Kandy$", r"Kandy", "direct"), (r"^Sri Lanka|^Khurdaka$", r"Ceylon", "direct"),
    (r"^Nepal$", r"Nepal|Bhanderia", "direct"), (r"^Krishnanagar$", r"Calcutta", "direct"),
    (r"^(Tibet|Sikkim|Bhutan)$", r"Darjeeling", "via"),
    (r"^Java$", r"Java|Batavia|Buitenzorg|Garut|Tjandjur|Tjipandak|Sindangbarang|Tanggeng", "direct"),
    (r"^Johor$", r"Johor|Singapore", "direct"),
    (r"^(New South Wales)$", r"Sydney|Narromine|Mullengudgery|Badgery", "direct"),
    (r"^(Papua Neuguinea|Neuguinea|Hood Bay|Milne Bay Province|Purari Delta|Madang)$", r"New Guinea|Port Moresby", "direct"),
    (r"^Aru$", r"Aru|Dobo", "direct"),
    (r"^(Tanimbar|Leti|Wetar|Babar|Romang|Seram|Wakollo|Halmahera)$", r"Amboina|Kajeli", "via"),
    (r"^(Borneo|Sarawak|Kalimantan|Brunei|.*Kalimantan.*)$", r"Kuching|Borneo", "via"),
    (r"^Überseeterritorium Frankreich$", r"Numea|New Caledonia", "direct"),
    (r"^Japan$", r"Japan|Nagasaki|Kumamoto|Kyoto|Tokyo|Nikko|Yokohama|Miyanoshita|Nagoya|Nara|Shimonoseki|Miyajima", "direct"),
    (r"^China$", r"Canton|Hongkong|Macao", "direct"), (r"^Aden$", r"Aden", "direct"),
    (r"^(Kanada|Nordamerika)$", r"Canada|United States", "direct"),
]
ROUTE_NOTE = {  # Henje's "Ortschaft (Route)" suggestion -> site place regex
    "Jaipur": r"Jaipur", "Hyderabad": r"Hyderabad|Tandur|Sikanderab", "Delhi": r"Delhi", "Gwalior": r"Gwalior",
    "Bombay": r"Bombay|Poona", "Kandy": r"Kandy", "Kajeli": r"Kajeli", "Tokyo": r"Tokyo", "Calcutta": r"Calcutta",
}
ACQ = re.compile(r"\b(kaufte|kauften|gekauft|Kauf|Ankauf|Einkäufe?|einzukaufen|erwarb|erworben|erstand|"
                 r"Geschenke?|schenkte|geschenkt|überreicht\w*|verehrt\w*|Andenken|Bazar|Händler|feilgeboten)\b", re.I)
CARD = [("gift_to_ff", r"[^/]{0,40}Geschenk[^/]{0,120}(Erzherzog|Franz.?Ferdinand|Thronfolger)[^/]{0,140}|"
                       r"[^/]{0,60}(Erzherzog|Franz.?Ferdinand)[^/]{0,80}geschenkt[^/]{0,80}"),
        ("occasion", r"anl[äa](ß|ss)lich[^/]{0,120}"), ("school_of_art", r"School of Art|Kunstschule"),
        ("collected_1893", r"\bS\.? ?189[23]\b|\b189[23]\b"), ("voyage", r"Weltreise")]
MATERIAL = re.compile(r"\b(Fell|Felle|Pelz|Rohhaut|Horn|Hörner|Geweih|Elfenbein|Zahn|Zähne|Krallen?|Feder\w*|"
                      r"Schildpatt|Perlmutt|Knochen|Schlangenhaut|Krokodilhaut|Tigerfell)\b", re.I)
GENERIC = {"figur", "mann", "frau", "höfisch", "kinderspielzeug", "teil", "objekt", "modell", "zwei", "paar",
           "klein", "kleine", "groß", "große", "großer", "alte", "neue", "deckel", "scheide", "stock", "band", "kopf",
           "bild", "platte", "gold", "silber", "messing", "kupfer", "eisen", "holz", "leder", "stein", "glas", "seide",
           "tibetan", "tibetanisch", "indisch", "indische", "japanisch", "japanische", "chinesisch", "javanisch"}
INFLECTION = ("", "e", "en", "er", "ern", "es", "s", "n")


def plain(w):
    """lower case, umlauts folded: Pulverhörner -> pulverhorner (plural with umlaut matches Pulverhorn)"""
    return w.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u")


def nouns(label):
    return {plain(w) for w in re.findall(r"[A-ZÄÖÜa-zäöüß]{4,}", label or "") if w.lower().rstrip(".") not in GENERIC}


def matches(nouns_, sentence):
    """Object word in the sentence, inflected but not as part of a compound (Dolch/Dolche, not Wasserlauf)."""
    hits = set()
    for t in re.findall(r"[A-ZÄÖÜa-zäöüß]{4,}", sentence):
        t = plain(t)
        for n in nouns_:
            if t.startswith(n) and t[len(n):] in INFLECTION:
                hits.add(n)
    return hits


def regions_of(o):
    out = []
    if o["Ortschaft (Route)"] != "NA":
        for note in o["Ortschaft (Route)"]:
            for k, rx in ROUTE_NOTE.items():
                if k.lower() in note.lower():
                    out.append({"region": note, "days_rx": rx, "kind": "direct", "from": "Ortschaft (Route)"})
    for g in o["Geografie"]:
        if g in SKIP_INDIA:
            continue
        for rx_reg, rx_day, kind in REGIONS:
            if re.search(rx_reg, g):
                out.append({"region": g, "days_rx": rx_day, "kind": kind, "from": "Geografie"})
                break
    seen, uniq = set(), []
    for r in out:
        if r["days_rx"] not in seen:
            seen.add(r["days_rx"])
            uniq.append(r)
    return uniq


def card_text(o):
    return " / ".join(t["text"].replace("\n", " / ") for t in (o["Transkription"] if o["Transkription"] != "NA" else []))


def main():
    objects = json.loads((NORM / "objekte.json").read_text())
    days = [d for d in json.loads((NORM / "tagebuch_tage.json").read_text())["days"] if d["text"]]
    sents = {d["date"]: re.split(r"(?<=[.!?;])\s+", d["text"]) for d in days}
    hunts = load("hunts.json")
    hunt_days = {d["date"]: h["id"] for h in hunts if h["region"] for d in h["diary"]}
    out = []
    for o in objects:
        text = " ".join([o["Objektbezeichnung"], o["Titel"], o["Material"], o["Beschreibung"], card_text(o)])
        regs = regions_of(o)
        stay, diary = [], []
        st = nouns(o["Objektbezeichnung"])
        for r in regs:
            ds = [d for d in days if d["place_site"] and re.search(r["days_rx"], d["place_site"])]
            if not ds:
                continue
            stay.append({"region": r["region"], "kind": r["kind"], "from": r["from"],
                         "first": ds[0]["date"], "last": ds[-1]["date"], "days": len(ds),
                         "dates": [d["date"] for d in ds]})
            for d in ds:
                for s in sents[d["date"]]:
                    if hit := matches(st, s):
                        diary.append({"date": d["date"], "place": d["place_site"], "scan": d["scan"],
                                      "page_url": d["page_url"], "match": sorted(hit),
                                      "acquisition": bool(ACQ.search(s)), "text": s[:400]})
        card = [{"kind": k, "text": m.group(0).strip()[:300]} for k, rx in CARD
                for m in [re.search(rx, card_text(o))] if m]
        animals = sorted({a["id"] for a in ANIMALS if re.search(a["pattern"], text, re.I)})
        material = sorted({m.lower() for m in MATERIAL.findall(" ".join([o["Material"], o["Titel"], o["Objektbezeichnung"]]))})
        # hunting episodes on the very days FF was at this stop (not the span first..last: Calcutta twice)
        hunts_here = sorted({hunt_days[d] for r in stay for d in r["dates"] if d in hunt_days})
        strength = ("strong" if any(x["acquisition"] for x in diary) or any(c["kind"] in ("gift_to_ff", "occasion") for c in card)
                    else "medium" if diary or any(c["kind"] in ("school_of_art", "collected_1893") for c in card)
                    else "place" if stay else "none")
        out.append({
            "id": o["_meta"]["id"], "inventory": o["Inventarnummer"], "type": o["Objektbezeichnung"], "title": o["Titel"],
            "dating": o["Datierung"], "material": o["Material"], "geography": o["Geografie"],
            "url": o["Weltmuseum-Link"], "image": (o["Bild-Link"] or [None])[0] if o["Bild-Link"] != "NA" else None,
            "stay": stay, "diary": sorted(diary, key=lambda x: (not x["acquisition"], x["date"]))[:5],
            "card": card, "animals": animals, "animal_material": material, "hunts_here": hunts_here,
            "strength": strength,
        })
    rank = {"strong": 0, "medium": 1, "place": 2, "none": 3}
    out.sort(key=lambda x: (rank[x["strength"]], x["stay"][0]["first"] if x["stay"] else "9", x["inventory"]))
    by = {}
    for x in out:
        by[x["strength"]] = by.get(x["strength"], 0) + 1
    save("objects.json", {
        "source": "normalization/json/objekte.json (Weltmuseum Wien, Sammlung Este, online objects)",
        "about": "Links between objects and the voyage are suggestions with evidence (stay, diary sentence, "
                 "index card, animal material); strength: strong = acquisition/gift sentence in the diary or gift "
                 "on the card, medium = type named in the diary at that stop or School of Art / 1893 on the card, "
                 "place = only the region matches a stop.",
        "summary": by, "objects": out})
    print(f"{len(out)} objects: {by}; with animal material/motif: "
          f"{sum(bool(x['animals'] or x['animal_material']) for x in out)}; at a hunting stop: {sum(bool(x['hunts_here']) for x in out)}")
    for x in [y for y in out if y["strength"] == "strong"][:25]:
        ev = x["diary"][0] if x["diary"] else None
        c = next((c for c in x["card"] if c["kind"] in ("gift_to_ff", "occasion")), None)
        print(f"  {x['inventory']:<14} {x['type'][:24]:<24} {(ev['date'] + ' ' + ev['text'][:110]) if ev and ev['acquisition'] else 'CARD: ' + (c['text'][:110] if c else '')}")


if __name__ == "__main__":
    main()
