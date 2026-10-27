"""Step 5: write the ANNO clippings into the prototype's press table.

Target: ../kaiserin_elisabeth/prototype/data/presse_anno.csv
(date,newspaper,page_url,place,quote,voice,added_by + event_date,episode,relevance)

Only issues with relevance "high" (a snippet names the archduke). `date` stays the
publication date; `event_date` is the diary day the report is about: the episode day whose
kill sentences mention the animal highlighted in the snippet most often. Rows entered by
hand (added_by not starting with "auto:") are kept; earlier auto rows are replaced.
"""
import csv
import json
import re

from common import ROOT, load

TARGET = ROOT.parent / "kaiserin_elisabeth" / "prototype" / "data" / "presse_anno.csv"
DIARY = ROOT.parent / "kaiserin_elisabeth" / "prototype" / "data" / "ke_diary.json"
AUTO = "auto: enrichment/02_anno.py"
BASE = ["date", "newspaper", "page_url", "place", "quote", "voice", "added_by"]
EXTRA = ["event_date", "episode", "relevance"]
ANIMALS = json.loads((ROOT / "animals.json").read_text())


def animals_marked(text):
    marks = " ".join(re.findall(r"<mark>(.*?)</mark>", text))
    return {a["id"] for a in ANIMALS if re.search(a["pattern"], marks, re.I)}


def event_day(entries, animals):
    return max(entries, key=lambda e: (sum(e["animals"].get(a, 0) for a in animals), e["kill_sentences"]))["date"]


def quote(text, limit=400):
    t = re.sub(r"</?mark>", "", text).strip(" .…")
    return t if len(t) <= limit else t[:limit].rsplit(" ", 1)[0] + " …"


def main():
    entries = load("hunt_entries.json")
    diary_place = {d["date"]: d.get("place") or d.get("place_as_printed") for d in json.loads(DIARY.read_text())}
    rows, seen = [], set()
    for ep in load("enrichment.json")["episodes"]:
        ep_entries = [e for e in entries if ep["start"] <= e["date"] <= ep["end"]]
        for a in ep["anno"]["articles"]:
            if a["relevance"] != "high" or (ep["id"], a["docId"]) in seen:
                continue
            seen.add((ep["id"], a["docId"]))
            s = next((s for s in a["snippets"] if animals_marked(s["text"])), a["snippets"][0])
            day = event_day(ep_entries, animals_marked(s["text"]))
            rows.append({
                "date": a["date"], "newspaper": re.sub(r"\s+\d{1,2}\.\s+\S+\s+\d{4}$", "", a["title"]),
                "page_url": s["url"], "place": diary_place.get(day) or ep["places"][0]["label"],
                "quote": quote(s["text"]), "voice": "Presse", "added_by": AUTO,
                "event_date": day, "episode": ep["id"], "relevance": a["relevance"],
            })

    manual = []
    if TARGET.exists():
        manual = [r for r in csv.DictReader(TARGET.open(encoding="utf-8-sig"))
                  if r.get("date") and not (r.get("added_by") or "").startswith("auto:")]
    with TARGET.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=BASE + EXTRA, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(manual + sorted(rows, key=lambda r: (r["event_date"], r["date"])))
    print(f"wrote {TARGET.relative_to(ROOT.parent)}: {len(manual)} manual + {len(rows)} auto rows")


if __name__ == "__main__":
    main()
