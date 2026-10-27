"""Step 1: find hunting passages in Franz Ferdinand's diary (OCR text) per dated entry.

A "kill sentence" is a sentence with a killing verb (erlegen, schießen, Strecke, Beute ...)
plus at least one animal from animals.json. Entries with kill sentences are grouped into
hunting episodes by place (places.json maps the OCR place names to a normalised key).

Output: data/hunt_entries.json (per diary entry), data/hunts.json (per episode)
"""
import json
import re
from collections import Counter
from datetime import date

from common import ROOT, SOURCES, save

ANIMALS = json.loads((ROOT / "animals.json").read_text())
PLACES = json.loads((ROOT / "places.json").read_text())

KILL = re.compile(r"erleg|geschoss|\bschoss|\bschoß|schöss|zur strecke|\bbeute\b|erbeut|schweißt|\bfehlte", re.I)
FIRST_PERSON = re.compile(r"\b(ich|mir|mich|meine[nmrs]?|mein)\b", re.I)
# elephants were mostly ridden ("vom Elephanten aus"), not shot
RIDING = re.compile(r"(auf|vom|von|mit|zu|die|den)\s+\S*\s*$", re.I)
HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2}) · (.*)$")
SCAN = re.compile(r"^\*Scan (\d+)\*")


def parse_diary(path, band):
    entries, cur, scan = [], None, None
    for line in path.read_text().splitlines():
        if m := SCAN.match(line):
            scan = int(m.group(1))
            continue
        if m := HEADING.match(line):
            cur = {"date": m.group(1), "place_raw": m.group(2).strip(), "band": band, "scan": scan, "text": []}
            entries.append(cur)
        elif line.startswith("## "):
            cur = None
        elif cur is not None:
            if cur["scan"] is None and scan:
                cur["scan"] = scan
            cur["text"].append(line)
    for e in entries:
        e["text"] = re.sub(r"\s+", " ", " ".join(e["text"])).strip()
    return entries


def animals_in(sentence):
    found = []
    for a in ANIMALS:
        for m in re.finditer(a["pattern"], sentence, re.I):
            if a["id"] == "elephant" and RIDING.search(sentence[: m.start()][-25:]):
                continue
            found.append(a["id"])
            break
    return found


def place_of(raw):
    low = raw.lower()
    for p in PLACES:
        if any(v.lower() in low for v in p["diary"]):
            return p
    return {"id": None, "region": None}


def main():
    entries = parse_diary(SOURCES / "FF Tagebuch Bd. 1.md", 1) + parse_diary(SOURCES / "FF Tagebuch Bd. 2.md", 2)
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
            "date": e["date"], "place_raw": e["place_raw"], "place_id": (pl := place_of(e["place_raw"]))["id"], "region": pl["region"],
            "band": e["band"], "scan": e["scan"],
            "animals": dict(counts.most_common()),
            "kill_sentences": len(kills),
            "first_person": sum(k["first_person"] for k in kills),
            "quotes": sorted(kills, key=lambda k: (not k["first_person"], -len(k["animals"])))[:4],
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
