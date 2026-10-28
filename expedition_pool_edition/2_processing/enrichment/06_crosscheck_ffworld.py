"""Step 6: cross-check the itinerary with franzferdinandsworld.com ("Franz Ferdinand's World Tour").

The site lists every day 14.12.1892–18.10.1893 with a place and (for 284 days) a page with
an English translation of that day's diary text. We compare
  - the site's place per day with Höfer's itinerary (../analyses/itinerary_1892_93.csv)
    and with the diary headings (../../3_visualization/web/data/ke_diary.json),
  - the site's days with our diary entries: an entry that spans several site days means
    the OCR missed inline date headings, so quotes dated by that entry may be days off.
Only dates, places and URLs are written out, not the site's text.

Output: data/ffworld_days.csv, data/ffworld_crosscheck.json
"""
import csv
import difflib
import html
import json
import re
import unicodedata
from datetime import date, timedelta

from common import ANALYSES, DATA, ROOT, WEB_DATA, get_text, save

SITE = "http://www.franzferdinandsworld.com/the-journey/"
MONTHS = {m: i + 1 for i, m in enumerate("January February March April May June July August September "
                                         "October November December".split())}
SEA = re.compile(r"\bat sea\b|\bnear\b|\bsea\b|ocean|gulf|reef|in see", re.I)
ALIAS = {"dschodpur": "jodhpur", "dscbodpur": "jodhpur", "dschaipur": "jaipur", "siriska": "sariska", "sirtska": "sariska",
         "dehli": "delhi", "dehii": "delhi", "haidarabad": "hyderabad", "dardschiling": "darjeeling", "numea": "noumea",
         "kioto": "kyoto", "tokio": "tokyo", "jokohama": "yokohama", "kanton": "canton", "hongkong": "hong kong",
         "singapur": "singapore", "triest": "trieste", "wien": "vienna", "schimonoseki": "shimonoseki",
         "tjiandjur": "tjandjur", "pentieton": "penticton", "amboina": "ambon", "steamer point": "aden"}
STOP = {"india", "nepal", "java", "japan", "china", "ceylon", "france", "egypt", "australia", "canada", "usa", "the",
        "near", "from", "with", "joint", "entry", "separate", "camp", "hunting", "islands", "island", "austria"}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = re.sub(r"[^a-z ]", " ", "".join(c for c in s if not unicodedata.combining(c)))
    for k, v in ALIAS.items():
        s = s.replace(k, v)
    return s


def words(s):
    return {w for w in norm(s).split() if len(w) > 3 and w not in STOP}


def site_days():
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", get_text(SITE), flags=re.S)
    rows, section = [], None
    for blk in re.split(r"<br\s*/?>|</p>|</h\d>|</li>", page):
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", blk))).strip()
        if re.match(r"^[IVXL]+\. ", txt):
            section = txt
        if m := re.search(r"(\d{1,2}) (%s) (189\d)\s*[:;]\s*(.+)$" % "|".join(MONTHS), txt):
            link = re.search(r'href="([^"]+)"', blk)
            url = link.group(1) if link else ""
            rows.append({"date": f"{m.group(3)}-{MONTHS[m.group(2)]:02d}-{int(m.group(1)):02d}",
                         "place": m.group(4).strip(), "section": section,
                         "url": ("http:" + url) if url.startswith("//") else url})
    return rows


def classify(site_place, other):
    if SEA.search(site_place) or SEA.search(other) or " – " in other:
        return "sea_or_leg"
    if not other.strip(" –|"):
        return "gap_in_other"
    a, b = norm(site_place), norm(other)
    if max((difflib.SequenceMatcher(None, x, y).ratio() for x in a.split() for y in b.split()), default=0) >= 0.75:
        return "spelling"
    return "review"


def main():
    days = site_days()
    with (DATA / "ffworld_days.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "place", "section", "url"], lineterminator="\n")
        w.writeheader()
        w.writerows(days)
    print(f"site: {len(days)} days {days[0]['date']}..{days[-1]['date']}, {sum(bool(d['url']) for d in days)} with a page")

    hoefer = list(csv.DictReader((ANALYSES / "itinerary_1892_93.csv").open(encoding="utf-8")))
    # the 170 OCR heading entries (ke_diary.json has all 309 days; ocr_entry marks the days with a heading)
    diary = {d["date"]: d for d in json.loads(
        (WEB_DATA / "ke_diary.json").read_text()) if d.get("ocr_entry", True)}
    out = {"hoefer": [], "diary": []}
    n = {"hoefer": 0, "diary": 0}
    for d in days:
        h = " | ".join(r["stay"] or f"{r['from']} – {r['to']}" for r in hoefer if r["date_from"] <= d["date"] <= r["date_to"])
        if h:
            n["hoefer"] += 1
            if not words(d["place"]) & words(h):
                out["hoefer"].append({"date": d["date"], "site": d["place"], "hoefer": h, "kind": classify(d["place"], h)})
        if (x := diary.get(d["date"])) and x["heading"]:
            n["diary"] += 1
            other = f"{x['heading']} {x.get('place') or ''}"
            if not words(d["place"]) & words(other):
                out["diary"].append({"date": d["date"], "site": d["place"], "diary": x["heading"],
                                     "kind": classify(d["place"], x["heading"])})

    # diary entries that span several site days (inline date headings lost in the OCR)
    entry_dates = sorted(diary)
    paged = sorted(d["date"] for d in days if d["url"])
    spans = []
    for i, e in enumerate(entry_dates):
        nxt = entry_dates[i + 1] if i + 1 < len(entry_dates) else "1893-10-19"
        covered = [p for p in paged if e <= p < nxt]
        if len(covered) > 1:
            spans.append({"entry": e, "heading": diary[e]["heading"], "site_days": covered})
    kinds = {}
    for k in ("hoefer", "diary"):
        kinds[k] = {}
        for x in out[k]:
            kinds[k][x["kind"]] = kinds[k].get(x["kind"], 0) + 1
    save("ffworld_crosscheck.json", {
        "source": SITE, "checked": str(date.today()),
        "summary": {
            "site_days": len(days), "site_pages": len(paged), "diary_entries": len(entry_dates),
            "hoefer_days_compared": n["hoefer"], "hoefer_disagreements": kinds["hoefer"],
            "diary_days_compared": n["diary"], "diary_disagreements": kinds["diary"],
            "diary_entries_spanning_several_site_days": len(spans),
            "site_days_inside_such_entries": sum(len(s["site_days"]) - 1 for s in spans),
        },
        "disagreements": out, "multi_day_entries": spans,
    })
    print(json.dumps(kinds, ensure_ascii=False))
    for k in ("hoefer", "diary"):
        for x in out[k]:
            if x["kind"] == "review":
                print(f"  review {k}: {x['date']}  site: {x['site']}  vs  {x.get('hoefer') or x.get('diary')}")
    print(f"{len(spans)} diary entries span several site days ({sum(len(s['site_days']) - 1 for s in spans)} extra days)")


if __name__ == "__main__":
    main()
