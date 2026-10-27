"""Step 1: find hunting passages in Franz Ferdinand's diary (OCR text) per day.

Input: ../normalization/json/tagebuch_tage.json – the diary split into days (diary_days.py; the
OCR headings alone give only 170 entries for ~284 days).

A "kill sentence" is a sentence with a killing verb (erlegen, schießen, zur Strecke, Beute ...)
plus at least one animal from animals.json. Days with kill sentences are grouped into
hunting episodes by region (places.json maps day places / OCR spellings to a place).

Output: data/hunt_entries.json (per day), data/hunts.json (per episode)
"""
import json
import re
from collections import Counter
from datetime import date

from common import ROOT, load, save

ANIMALS = json.loads((ROOT / "animals.json").read_text())
PLACES = load("places_resolved.json")

KILL = re.compile(r"erleg|geschoss|\bschoss|\bschoß|schöss|zur strecke|\bbeute\b|erbeut|schweißt|\bfehlte", re.I)
FIRST_PERSON = re.compile(r"\b(ich|mir|mich|meine[nmrs]?|mein)\b", re.I)
# elephants were mostly ridden ("vom Elephanten aus"), not shot
RIDING = re.compile(r"(auf|vom|von|mit|zu|die|den)\s+\S*\s*$", re.I)
DAYS = ROOT.parent / "normalization" / "json" / "tagebuch_tage.json"


def diary_days():
    return [d for d in json.loads(DAYS.read_text())["days"] if d["text"]]


def animals_in(sentence):
    found = []
    for a in ANIMALS:
        for m in re.finditer(a["pattern"], sentence, re.I):
            if a["id"] == "elephant" and RIDING.search(sentence[: m.start()][-25:]):
                continue
            found.append(a["id"])
            break
    return found


def place_of(*names):
    """First place whose diary/OCR spelling occurs in the day's place (site) or the OCR heading."""
    for raw in names:
        low = (raw or "").lower()
        for p in PLACES:
            if any(v.lower() in low for v in p["diary"]):
                return p
    return {"id": None, "region": None}


def main():
    entries = diary_days()
    out = []
    for e in entries:
        kills = []
        for s in re.split(r"(?<=[.!?;])\s+", e["text"]):
            if KILL.search(s) and (ids := animals_in(s)):
                kills.append({"text": s[:400], "animals": ids, "first_person": bool(FIRST_PERSON.search(s))})
        if not kills:
            continue
        counts = Counter(a for k in kills for a in k["animals"])
        out.append({
            "date": e["date"], "place_raw": e["place_site"] or e["heading_ocr"],
            "place_id": (pl := place_of(e["place_site"], e["heading_ocr"]))["id"], "region": pl["region"],
            "band": e["band"], "scan": e["scan"], "page_url": e["page_url"], "day_method": e["method"],
            "animals": dict(counts.most_common()),
            "kill_sentences": len(kills),
            "first_person": sum(k["first_person"] for k in kills),
            "quotes": sorted(kills, key=lambda k: (not k["first_person"], -len(k["animals"])))[:4],
            "kills": [k["text"] for k in kills],   # all kill sentences (for who was there: 03c_people)
        })
    save("hunt_entries.json", out)

    # episodes: consecutive hunt entries in the same region (gap <= 6 days)
    episodes = []
    for e in out:
        last = episodes[-1] if episodes else None
        if (last and e["region"] and e["region"] == last["region"]
                and (date.fromisoformat(e["date"]) - date.fromisoformat(last["end"])).days <= 6):
            last["end"] = e["date"]
            last["entries"].append(e)
        else:
            episodes.append({"region": e["region"], "start": e["date"], "end": e["date"], "entries": [e]})
    hunts = []
    for ep in episodes:
        counts = Counter()
        for e in ep["entries"]:
            counts.update(e["animals"])
        weight = sum(e["kill_sentences"] for e in ep["entries"])
        hunts.append({
            "id": f"hunt-{ep['start']}-{ep['region'] or 'unknown'}",
            "region": ep["region"],
            "place_ids": list(dict.fromkeys(e["place_id"] for e in ep["entries"] if e["place_id"])),
            "place_raw": ep["entries"][0]["place_raw"],
            "start": ep["start"], "end": ep["end"],
            "animals": dict(counts.most_common()),
            "kill_sentences": weight,
            "diary": [{"date": e["date"], "band": e["band"], "scan": e["scan"]} for e in ep["entries"]],
            "quotes": [dict(q, date=e["date"], band=e["band"], scan=e["scan"])
                       for e in ep["entries"] for q in e["quotes"][:2]][:6],
        })
    save("hunts.json", hunts)
    print(f"{len(out)} diary entries with hunting, {len(hunts)} episodes")
    for h in hunts:
        print(f"  {h['start']}..{h['end']}  {h['region'] or '?':<13} {h['place_raw'][:28]:<28} {h['kill_sentences']:>3}  {h['animals']}")


if __name__ == "__main__":
    main()
