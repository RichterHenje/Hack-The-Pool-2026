"""Step 3b: Höfer's itinerary and photographs of the voyage per hunting episode.

Inputs from the team's analysis layer (../Analysen/, see its README):
  itinerary_1892_93.csv  dated stages/stays from Höfer (ed.), Imperial Sightseeing, 2010
  vf_weltmuseum.csv      VF photo numbers matched to Weltmuseum Wien object pages

Per episode:
  hoefer  - the stays whose name matches the episode's places (diary spellings) and that
            overlap the episode ±7 days; their span can be longer than the diary's
            (e.g. Nepal: Höfer from 8 March, diary hunting from 10 March)
  photos  - Weltmuseum photos (verified/variants) dated inside the Höfer or diary span,
            plus public-domain photos found on Wikimedia Commons (API search, dated
            via DateTimeOriginal). Weltmuseum images: link only, rights not stated.

Output: data/hoefer_photos.json
"""
import csv
import json
import re
import unicodedata
from datetime import date, timedelta

from common import ROOT, get_json, load, save

ANALYSEN = ROOT.parent / "Analysen"
PLACES = {p["id"]: p for p in load("places_resolved.json")}
MONTHS = {"jänner": 1, "januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6,
          "juli": 7, "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12}
COMMONS = "https://commons.wikimedia.org/w/api.php"
COMMONS_QUERIES = ["Franz Ferdinand 1893 Ceylon", "Franz Ferdinand Elefantenjagd", "Franz Ferdinand Tiger 1893",
                   "Franz Ferdinand Indien 1893", "Franz Ferdinand Nepal 1893", "Franz Ferdinand Australien 1893",
                   "Franz Ferdinand Java 1893", "Hodek Franz Ferdinand"]
PAD = timedelta(days=7)


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def museum_date(s):
    """(start, end) from Weltmuseum dates like '22.III.1893', '24.1.1893', '24. Januar 1893',
    '19.–24. April1893'; None when only a year or month is given."""
    s = norm(s or "").replace("–", "-")
    if m := re.search(r"(\d{1,2})\.\s*-\s*(\d{1,2})\.\s*([a-z]+)\s*(\d{4})", s):
        if (mo := MONTHS.get(m.group(3))):
            return date(int(m.group(4)), mo, int(m.group(1))), date(int(m.group(4)), mo, int(m.group(2)))
    if m := re.search(r"(\d{1,2})\.\s*([ivx]+|\d{1,2})\.\s*(\d{4})", s):
        mo = ROMAN.get(m.group(2)) or int(m.group(2))
        d = date(int(m.group(3)), mo, int(m.group(1)))
        return d, d
    if m := re.search(r"(\d{1,2})\.\s*([a-z]+)\s*(\d{4})", s):
        if (mo := MONTHS.get(m.group(2))):
            d = date(int(m.group(3)), mo, int(m.group(1)))
            return d, d
    return None


def hoefer_stays(h, stays):
    names = [norm(v) for p in h["place_ids"] for v in PLACES[p]["diary"]]
    s0, e0 = date.fromisoformat(h["start"]) - PAD, date.fromisoformat(h["end"]) + PAD
    out = []
    for r in stays:
        a, b = date.fromisoformat(r["date_from"]), date.fromisoformat(r["date_to"])
        n = norm(r["stay"])
        if a <= e0 and b >= s0 and any(x in n or n in x for x in names):
            out.append({"stay": r["stay"], "from": r["date_from"], "to": r["date_to"], "section": r["section"]})
    return out


def commons_photos():
    titles = set()
    for q in COMMONS_QUERIES:
        r = get_json(COMMONS, {"action": "query", "list": "search", "srsearch": q, "srnamespace": 6,
                               "srlimit": 20, "format": "json"})
        titles |= {x["title"] for x in r["query"]["search"] if re.search(r"\.(jpe?g|png|tiff?)$", x["title"], re.I)}
    photos = []
    for t in sorted(titles):
        r = get_json(COMMONS, {"action": "query", "titles": t, "prop": "imageinfo",
                               "iiprop": "url|extmetadata", "iiurlwidth": 640, "format": "json"})
        ii = next(iter(r["query"]["pages"].values()))["imageinfo"][0]
        m = {k: re.sub(r"<[^>]+>", "", str(v.get("value", ""))).strip() for k, v in ii["extmetadata"].items()}
        d = re.match(r"(\d{4}-\d{2}-\d{2})", m.get("DateTimeOriginal", ""))
        if not d or "Franz Ferdinand" not in (m.get("ImageDescription", "") + t):
            continue
        photos.append({
            "source": "Wikimedia Commons", "title": m.get("ObjectName") or t.removeprefix("File:"),
            "description": m.get("ImageDescription", "")[:300], "date": d.group(1),
            "creator": m.get("Artist"), "credit": m.get("Credit"), "rights": m.get("LicenseShortName"),
            "url": ii["descriptionurl"], "image": ii.get("thumburl"),
        })
    return photos


def weltmuseum_photos():
    out = []
    for r in csv.DictReader((ANALYSEN / "vf_weltmuseum.csv").open(encoding="utf-8")):
        if r["status"] not in ("verified", "variants_only") or not (span := museum_date(r["museum_date"])):
            continue
        out.append({
            "source": "Weltmuseum Wien", "vf_id": r["vf_id"], "title": r["museum_title"],
            "date": span[0].isoformat(), "date_to": span[1].isoformat(), "status": r["status"],
            "geography": r["museum_geography"], "url": r["url"], "rights": None, "image": None,
            "note": "VF number from Höfer 2010, matched by the team (Analysen/vf_weltmuseum.csv)",
        })
    return out


def main():
    stays = [r for r in csv.DictReader((ANALYSEN / "itinerary_1892_93.csv").open(encoding="utf-8")) if r["stay"]]
    photos = weltmuseum_photos() + commons_photos()
    print(f"photos with a day date: {len(photos)} "
          f"(Weltmuseum {sum(p['source'] == 'Weltmuseum Wien' for p in photos)}, "
          f"Commons {sum(p['source'] == 'Wikimedia Commons' for p in photos)})")
    episodes = []
    for h in load("hunts.json"):
        if not h["region"]:
            continue
        hs = hoefer_stays(h, stays)
        a = min([h["start"]] + [s["from"] for s in hs])
        b = max([h["end"]] + [s["to"] for s in hs])
        diary_days = {d["date"] for d in h["diary"]}
        span_days = {(date.fromisoformat(a) + timedelta(days=i)).isoformat()
                     for i in range((date.fromisoformat(b) - date.fromisoformat(a)).days + 1)}
        linked = [p for p in photos if a <= p["date"] <= b or (p.get("date_to") and a <= p["date_to"] <= b)]
        episodes.append({
            "hunt_id": h["id"],
            "hoefer": {"stays": hs, "from": a, "to": b,
                       "days_without_hunting_entry": len(span_days - diary_days),
                       "diary_within_hoefer": bool(hs) and hs[0]["from"] <= h["start"] and h["end"] <= max(s["to"] for s in hs)},
            "photos": sorted(linked, key=lambda p: p["date"]),
        })
        if hs or linked:
            print(f"  {h['id']:<32} höfer {a}..{b} ({len(hs)} stays)  photos {len(linked)}")
    save("hoefer_photos.json", {
        "sources": {"hoefer": "Regina Höfer (Hg.), Imperial Sightseeing, Wien 2010, doi:10.11588/xarep.00001404 "
                              "(via Kriegsmarine/Analysen/itinerary_1892_93.csv)",
                    "weltmuseum": "Weltmuseum Wien, Online-Sammlung (via Kriegsmarine/Analysen/vf_weltmuseum.csv)",
                    "commons": "Wikimedia Commons API"},
        "episodes": episodes,
    })


if __name__ == "__main__":
    main()
