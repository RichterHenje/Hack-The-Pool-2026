"""Layers "Menschen" and "Sammeln" for the travel page: joins onto the diary days.

    uv run python -m scripts.ke_layers --vault <vault_dir> --sources <dir> --out <file.json>
                                       [--disable J1,J2,J3]

<sources> holds "FF Tagebuch Bd. 1.md", "FF Tagebuch Bd. 2.md" (day-segmented diary) and
kaiserin_elisabeth_ranglisten.csv (crew lists). Joins (docs/control_battery_layers.md):
  J1 aboard: rows of the latest crew-list issue dated <= day, with `seit` empty or <= day
  J2 local actors: person/company notes linking to the vault place note the day's location
     refers to (location = last part of a transfer heading; "In See …" days have none)
  J3 collecting: diary sentences with an acquisition verb AND an object word
Voyage-level (not per day): medal holders (Seereise-Denkmünze 1892/1893), curated Kulturpool
records, Weltmuseum photo numbers from Höfer 2010 (facts only).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kp import geo
from scripts.ke_diary import SPELLINGS, kind_of, location_of, sentences
from scripts.vault_clean import SHIP_PREFIX, split_frontmatter
from scripts.vault_clean import key as name_key

NOT_ACTOR = re.compile(SHIP_PREFIX.pattern + r"|weltreise|eskader|reise\b", re.IGNORECASE)

ACQ = re.compile(
    # widened after blind loop 1 (missed "erstand", "erhielt … als Geschenk", "meiner Sammlung")
    r"\b(erw[aoi]rb\w*|erworben|kaufte\w*|gekauft|kaufen|einkauf\w*|angeboten|anbot|"
    r"erstand\w*|erstanden|erstehen|erhielt\w*|erhalten|bekam|bekommen|"
    r"schenkte\w*|geschenkt\w*|geschenk\w*|beschenkt\w*|überreicht\w*|verehrt\w*|"
    r"eintausch\w*|eingetauscht|tauschte\w*|erbeutet\w*|"
    r"sammelte\w*|gesammelt|sammeln|präpar\w*|ausgestopft|ausstopfen|"
    r"mitgenommen|mitnahm|verpackt\w*|bereicherung|"
    r"(?:für|in|zu|meiner|unserer|die|der) (?:meine |unsere )?Sammlung|als Andenken|zum Andenken)\b",
    re.IGNORECASE,
)
OBJ = re.compile(
    r"(sammlung|exemplar|waffe|fetisch|schmuck|gegenst[aä]nd|kuriosit|curiosit|\bhaut\b|häute|"
    r"fell|gehörn|geweih|trophä|bälge|\bbalg|skelett|vogel|vögel|insekt|schmetterling|muschel|"
    r"ethnograph|figur|götze|maske|speer|bogen|pfeil|keule|ruder|canoe|kanu|photograph|andenken)",
    re.IGNORECASE,
)


def readable(s: str) -> bool:
    """Drop OCR garbage (index pages): mostly letters and spaces, few odd characters."""
    if len(s) < 25:
        return False
    good = sum(c.isalpha() or c.isspace() or c in ".,;:-–—'\"()!?" for c in s)
    words = re.findall(r"[^\W\d_]+", s)
    real = [w for w in words if len(w) >= 3 and (w.islower() or w.istitle())]
    # OCR garbage has many short fragments and mixed-case tokens ("en gen ommend lconsul")
    return (
        good / len(s) >= 0.93
        and s.count("^") == 0
        and len(words) >= 5
        and len(real) / len(words) >= 0.7
    )


def line_ok(line: str) -> bool:
    """A text line, not OCR debris ("m r-^'t -v.f -^9^v .^")."""
    # Share of odd characters, not their presence: OCR scatters single "^" through long
    # prose lines (a presence test dropped 58% of the diary text).
    s = line.strip()
    if not s:
        return True
    letters = sum(c.isalpha() for c in s)
    odd = sum(not (c.isalpha() or c.isspace() or c in ".,;:-–—'\"()!?»«„“”") for c in s)
    return letters >= 0.5 * len(s) and odd <= 0.15 * len(s)


def parse_diary(sources: Path) -> list[dict]:
    days = []
    for band in ("1", "2"):
        cur = None
        for line in (
            (sources / f"FF Tagebuch Bd. {band}.md").read_text(encoding="utf-8-sig").splitlines()
        ):
            h = re.match(r"^### (\d{4}-\d{2}-\d{2})(?:\s*·\s*(.*))?$", line)
            if h:
                cur = {"date": h.group(1), "heading": (h.group(2) or "").strip(), "text": []}
                days.append(cur)
            elif cur is not None and not line.startswith("#"):
                # Page breaks: skip the marker line ("*S. 227 · Scan 240*") and OCR-garbage
                # lines, which otherwise merge into the next sentence (blind loop 2: a planted
                # sentence after a page break was lost this way).
                if re.match(r"^\s*\*(?:S\.\s*\S+\s*·\s*)?Scan \d+\*", line):
                    continue
                clean = re.sub(r"\s*\^scan\d+\s*$", "", line)
                if clean.strip() and not line_ok(clean):
                    continue
                cur["text"].append(clean)
    days.sort(key=lambda d: d["date"])
    for d in days:
        k = kind_of(d["heading"])
        d["location"] = location_of(d["heading"], k)
    return days


def place_index(vault: Path) -> dict[str, list[str]]:
    """normalised name -> vault place note titles (first part, stated modern and historic names)."""
    idx = defaultdict(list)
    for p in (vault / "Ortschaften").glob("*.md"):
        if p.stem.startswith("0_"):
            continue
        t = p.stem
        names = {re.split(r"[,(]", t)[0].strip(), *geo.historic_names(t)}
        names |= {m for m in re.findall(r"heut\.?\s*([^,;()]+)", t, re.IGNORECASE)}
        for n in names:
            if n.strip():
                idx[geo.norm(n.strip())].append(t)
    return idx


def place_of(location: str, idx: dict) -> str | None:
    if not location:
        return None
    for cand in (location, SPELLINGS.get(geo.norm(location), "")):
        hits = sorted(set(idx.get(geo.norm(cand), []))) if cand else []
        if len(hits) == 1:
            return hits[0]
    return None


def crew(sources: Path) -> list[dict]:
    path = sources / "kaiserin_elisabeth_ranglisten.csv"
    return list(csv.DictReader(path.open(encoding="utf-8-sig"), delimiter=";"))


def aboard(rows: list[dict], day: str) -> tuple[str, list[dict]]:
    issues = sorted({r["ausgabe"] for r in rows if r["ausgabe"] <= day})
    if not issues:
        return "", []
    latest = issues[-1]
    return latest, [
        r for r in rows if r["ausgabe"] == latest and (not r["seit"] or r["seit"] <= day)
    ]


def actors(vault: Path) -> dict[str, list[dict]]:
    """place note title -> notes (Personen, Firmen) linking to it."""
    out = defaultdict(list)
    for folder in ("Personen", "Firmen_Dienstleister_Institutionen"):
        for p in (vault / folder).glob("*.md"):
            # ship and event notes filed under Personen are not actors (the world-tour note
            # links every place and would show up on every day)
            if p.stem.startswith("0_") or NOT_ACTOR.search(p.stem):
                continue
            text = p.read_text(encoding="utf-8-sig", errors="replace")
            text = split_frontmatter(text, "\r\n" if "\r\n" in text else "\n")[1]
            for t in {m.strip() for m in re.findall(r"\[\[([^\]|#]+)", text)}:
                out[t].append({"note": p.stem, "folder": folder})
    return out


KONTEXT = Path("analysis/ke_kulturpool_kontext.md")
HOEFER = Path("analysis/ke_research/hoefer_link/vf_photo_ids.csv")


def kulturpool_context() -> list[dict]:
    """Curated Kulturpool records (analysis/ke_kulturpool_kontext.md): table rows with a link.
    Voyage-level context, never attached to a day by place name."""
    if not KONTEXT.exists():
        return []
    out, section = [], ""
    for line in KONTEXT.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        m = re.search(r"https://kulturpool\.at/objekte/[0-9a-f-]{36}", line)
        if m and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            cells = [re.sub(r"\*+", "", c) for c in cells]  # drop Markdown emphasis
            out.append({"section": section, "label": cells[0], "text": cells[1], "url": m.group(0)})
    return out


def hoefer_photos() -> list[dict]:
    """Weltmuseum photo numbers from Höfer 2010 that name a stop (facts only, no images)."""
    if not HOEFER.exists():
        return []
    rows = csv.DictReader(HOEFER.open(encoding="utf-8"))
    return [
        {"vf_id": r["vf_id"], "page": r["hoefer_page_inferred"], "stops": r["stops_named_on_page"]}
        for r in rows
        if r.get("stops_named_on_page")
    ]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, required=True)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--disable", default="")
    ap.add_argument("--js", type=Path, default=None, help="also write window.KEL = … for the page")
    a = ap.parse_args(argv)
    off = {x.strip().upper() for x in a.disable.split(",") if x.strip()}
    days = parse_diary(a.sources)
    idx, rows, act = place_index(a.vault), crew(a.sources), actors(a.vault)
    medal = sorted(
        p.stem
        for p in (a.vault / "Personen").glob("*.md")
        if "Seereise-Denkm" in p.read_text(encoding="utf-8-sig", errors="replace")
    )
    medal_keys = {name_key(m): m for m in medal}
    out_days = {}
    for d in days:
        entry = {"heading": d["heading"], "location": d["location"]}
        if "J1" not in off:
            issue, on = aboard(rows, d["date"])
            entry["aboard_issue"] = issue
            entry["aboard"] = [
                {
                    "name": r["name"],
                    "rank": r["dienstgrad"],
                    "seit": r["seit"],
                    "medal_note": medal_keys.get(name_key(r["name"]), ""),
                }
                for r in on
            ]
            entry["aboard_by_rank"] = dict(Counter(r["dienstgrad"] for r in on).most_common())
        if "J2" not in off:
            place = place_of(d["location"], idx)
            entry["place_note"] = place or ""
            entry["actors"] = act.get(place, []) if place else []
        if "J3" not in off:
            # one paragraph per line in these files: a line break is a hard sentence boundary
            # (running headers and OCR debris otherwise merge into the next sentence)
            entry["collecting"] = [
                s[:400]
                for line in d["text"]
                for s in sentences(line)
                if readable(s) and ACQ.search(s) and OBJ.search(s)
            ]
        out_days[d["date"]] = entry
    result = {
        "days": out_days,
        "voyage": {
            "medal_holders": medal,
            "kulturpool_context": kulturpool_context(),
            "hoefer_photos": hoefer_photos(),
        },
        "rules": {
            "aboard": "latest crew-list issue dated on or before the day; rows with 'seit' after the day left out",
            "actors": "notes in Personen/Firmen that link to the day's place note",
            "collecting": "diary sentences with an acquisition verb and an object word (OCR garbage dropped)",
        },
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.js:
        a.js.write_text(
            "window.KEL = " + json.dumps(result, ensure_ascii=False) + ";\n", encoding="utf-8"
        )
    n_act = sum(1 for e in out_days.values() if e.get("actors"))
    n_col = sum(1 for e in out_days.values() if e.get("collecting"))
    n_place = sum(1 for e in out_days.values() if e.get("place_note"))
    print(
        f"{len(out_days)} days; with place note {n_place}; with actors {n_act}; "
        f"with collecting sentences {n_col}; medal holders {len(medal)} -> {a.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
