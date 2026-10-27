"""Step 7: the animals that survived – resolve the hand-curated heroes.json.

heroes.json lists the live animals of the voyage (the "Bordmenagerie" and animals sent to
Vienna) with diary quotes and ANNO clippings. This step
  - checks every quote against its source (diary entry of that date / ANNO snippets of
    that issue and page) and fails if one is not found,
  - adds links: diary scan (archive.org, from normalization/json/tagebuch_tage.json) and ANNO page,
  - adds coordinates to each route stop (heroes.json places, else places.json).

Output: data/heroes.json, data/heroes.geojson (one LineString per animal's journey)
"""
import html
import json
import re

import csv

from common import DATA, ROOT, get_json, get_text, load, save

HEROES = json.loads((ROOT / "heroes.json").read_text())
PLACES = {p["id"]: p for p in load("places_resolved.json")} | HEROES["places"]
DIARY_DAYS = {d["date"]: d for d in json.loads(
    (ROOT.parent / "normalization" / "json" / "tagebuch_tage.json").read_text())["days"]}
SNIPPET = "https://anno.onb.ac.at/anno-suche/rest/search/snippet"
NEWSPAPERS = {"nwg": "Neues Wiener Tagblatt", "gre": "Grazer Volksblatt", "msp": "Mährisch-Schlesische Presse",
              "kvb": "Kremser Volksblatt", "ibn": "Innsbrucker Nachrichten", "waz": "Wiener Allgemeine Zeitung"}


def squash(s):
    return re.sub(r"[^0-9a-zäöüß]", "", html.unescape(s).replace("\u00ad", "").lower())


def diary_entries():
    return {d: squash(x["text"]) for d, x in DIARY_DAYS.items()}


# ANNO returns ~3 snippets per page and which ones depends on the query, so the quotes were
# assembled from several queries; the check uses the same set (all cached from the research)
RESEARCH_QUERIES = [
    "Affen OR Affe OR Tiger OR Bären OR Bär OR Kakadu OR Kakadus OR Papageien OR Schwein OR Wildschwein OR Thiere OR "
    "Menagerie OR Kraus OR Erzherzog OR Hirsch OR Vögel OR Hühner OR Hahn OR Löwen OR Panther OR Exemplar OR Katze OR "
    "Konopischt OR Schönbrunn OR Triest OR Ziege OR Eichhörnchen OR Mainas OR Hyderabad OR Japan OR Biaggio OR Aufseher",
    "Schleichkatze OR Schleichkatzen OR Plumplori OR Lori OR Wildkatze OR Panther OR Johore OR Sultan OR Stück OR "
    "Geschenke OR Kasuar OR Hirsch OR Kakadu OR Kakadus OR Hühner OR Bären OR Antilope OR Gazelle OR Schlange OR Krokodil "
    "OR Leopard OR Pavian OR Makaken OR Schweinsaffen OR Gibbon OR Orang OR Papagei OR Vogel OR Hahn OR Zwerghühner OR "
    "Biaggio OR Aufseher OR Wärter OR Ragusaner OR Weltreise OR erworben OR käuflich OR Tiger OR Löwen OR Konopischt",
    "zahm OR Hunde OR Käfig OR Riesenschlange OR todt OR Bären OR japanische OR Kakadus OR Hühner OR Affen OR Hirsche OR "
    "Kasuare OR Kängurus OR Känguruhs OR Wallaby OR Papageien OR Leoparden OR Panther OR Schweine OR Hirsch OR Antilopen "
    "OR Vögel OR Fasanen OR Pfauen OR Bär OR Stachelschwein OR Ziege OR Löwe OR Gepard",
    "Thiere OR Sendung OR Affen OR Affe OR Fips OR Mucki OR Schönbrunn OR Menagerie OR Triest OR Lloyd OR Hongkong OR "
    "Papageien OR Kakadus OR Vögel OR lebende OR Exemplare OR Schwein OR Eichhörnchen OR Katze OR Jagdtrophäen OR Kraus "
    "OR Wärter OR Käfig OR Bord OR Makaken OR Pavian",
    "Affen OR Schönbrunn OR Menagerie", "Panther OR Johore OR Jahore", "Bären OR Bär OR Jesso OR japanischen",
    "Biaggio", "Thiere OR Affen OR Schönbrunn OR Triest",
    "Lori OR Erzlori OR Frauenlori OR Papageiengattungen OR Kakadus OR Hunde OR zugrunde OR Seereise OR Kängurus OR "
    "Känguruh OR Emu OR Wallaby OR Beutelthiere OR Opossum OR Tauben OR Fasanen",
]


def anno_text(doc, page):
    seen = set()
    for q in RESEARCH_QUERIES:
        s = get_json(SNIPPET, {"documentId": doc, "query": q})
        seen |= {squash(re.sub(r"<[^>]+>", "", x["text"])) for p in s.get("snippetPages", [])
                 for x in p["snippets"] if str(x["page"]) == str(page)}
    return " ".join(seen)


def coverage(p):
    """Share of 25-character pieces of the quote found in that page's snippets. Snippets are
    short windows starting mid-sentence and a quote may span two of them, so test pieces."""
    text = anno_text(p["doc"], p["page"])
    q = squash(p["quote"].replace("…", ""))
    pieces = [q[i:i + 25] for i in range(0, max(1, len(q) - 24), 25)]
    return sum(x in text for x in pieces) / len(pieces)


SITE_DAYS = {r["date"]: r for r in csv.DictReader((DATA / "ffworld_days.csv").open(encoding="utf-8"))}


def site(q):
    """English translation on franzferdinandsworld.com; URL by day from step 06."""
    return q | {"url": SITE_DAYS[q["day"]]["url"], "source": "franzferdinandsworld.com"}


def check_site(q):
    return squash(q["quote"])[:80] in squash(re.sub(r"<[^>]+>", " ", get_text(site(q)["url"])))


def press(p):
    acr, ymd = re.match(r"ANNO_([a-z]+)(\d{8})", p["doc"]).groups()
    return p | {"newspaper": NEWSPAPERS.get(acr, acr), "date": f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}",
                "url": f"https://anno.onb.ac.at/cgi-content/anno?aid={acr}&datum={ymd}&seite={p['page']}"}


def diary(q):
    day = DIARY_DAYS.get(q["date"], {})
    return q | {"band": day.get("band"), "scan": day.get("scan"), "page_url": day.get("page_url")}


def stop(s):
    p = PLACES[s["place"]]
    return s | {"label": p["label"], "lat": p["lat"], "lon": p["lon"], "wikidata": p.get("wikidata"),
                "coord_note": p.get("coord_note")}


def main():
    entries = diary_entries()
    problems = []
    for h in HEROES["people"] + HEROES["heroes"] + [{"id": "summary", "press": HEROES["summary_press"]}]:
        for q in h.get("diary", []):
            if squash(q["quote"])[:60] not in entries.get(q["date"], ""):
                problems.append(f"{h['id']}: diary {q['date']} not found: {q['quote'][:50]}")
        for q in h.get("site", []):
            if not check_site(q):
                problems.append(f"{h['id']}: site {q['day']} not found: {q['quote'][:50]}")
        for p in h.get("press", []):
            if (c := coverage(p)) < 0.8:
                problems.append(f"{h['id']}: press {p['doc']} p.{p['page']} only {c:.0%} found: {p['quote'][:50]}")
    if problems:
        raise SystemExit("quote check failed:\n  " + "\n  ".join(problems))

    heroes = [h | {"diary": [diary(q) for q in h.get("diary", [])],
                   "press": [press(p) for p in h.get("press", [])],
                   "site": [site(q) for q in h.get("site", [])],
                   "route": [stop(s) for s in h["route"]]}
              | ({"intended": h["intended"] | {k: PLACES[h["intended"]["place"]][k] for k in ("lat", "lon", "wikidata")}}
                 if h.get("intended") else {}) for h in HEROES["heroes"]]
    people = [h | {"diary": [diary(q) for q in h.get("diary", [])], "press": [press(p) for p in h.get("press", [])],
                   "site": [site(q) for q in h.get("site", [])]}
              for h in HEROES["people"]]
    save("heroes.json", {"about": HEROES["about"], "people": people, "heroes": heroes,
                         "summary_press": [press(p) for p in HEROES["summary_press"]]})
    save("heroes.geojson", {"type": "FeatureCollection", "features": [
        {"type": "Feature",
         "geometry": {"type": "LineString" if len(h["route"]) > 1 else "Point",
                      "coordinates": [[s["lon"], s["lat"]] for s in h["route"]] if len(h["route"]) > 1
                      else [h["route"][0]["lon"], h["route"][0]["lat"]]},
         "properties": {"id": h["id"], "name": h["name"], "species": h["species_de"], "status": h["status"],
                        "evidence": h["evidence"]}} for h in heroes]})
    by = {}
    for h in heroes:
        by[h["status"]] = by.get(h["status"], 0) + 1
    print(f"{len(heroes)} heroes, all quotes verified; by status: {by}")


if __name__ == "__main__":
    main()
