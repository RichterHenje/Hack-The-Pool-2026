"""Which entities of the team vault does Kulturpool already know? Which are new?

    uv run python -m scripts.vault_vs_kulturpool [vault_dir]

For every note in Personen, Firmen_Dienstleister_Institutionen, Schiffe,
Sammlungen_Projekte and Ortschaften (templates "0_Muster*" skipped) it runs two
Kulturpool searches:
  strict  exact phrase of the most specific form ("Alois Becker", "SMS Panther", ...)
  loose   exact phrase of the bare name ("Becker", "Panther")
and records hits, top providers and one example. A hit means the string occurs in a
record, not that it is the same person/ship: "present" rows need a human look.
"absent" (0 strict and 0 loose) is the strong signal: the vault knows something
Kulturpool's text does not contain at all.

Output: analysis/vault_vs_kulturpool.csv (tracked) and a summary on stdout.
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

from kp import geo
from kp import kulturpool as kpa
from scripts.vault_places import VAULT

FOLDERS = [
    "Personen",
    "Firmen_Dienstleister_Institutionen",
    "Schiffe",
    "Sammlungen_Projekte",
    "Ortschaften",
]
SHIP_TYPES = r"(Kreuzer|Korvette|Corvette|Kanonenbo(?:o)?t|Fregatte|Schiff)"
TITLES = r"\b(Dr\.|Prof\.|Graf|Freiherr|Ritter|Ritt\.|Edl\.|Mr\.|Captain|von|v\.)\s*"


def queries(folder: str, name: str) -> tuple[str, str]:
    """(strict phrase, loose phrase) for a note title."""
    if folder == "Personen" and "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        first_clean = re.sub(TITLES, "", first).strip(" ,.")
        strict = f"{first_clean} {last}".strip() if first_clean else last
        return strict, last
    if folder == "Schiffe":
        base = re.sub(rf",?\s*{SHIP_TYPES}\.?$", "", name, flags=re.IGNORECASE).strip(" ,")
        base = re.sub(r"^(H\.M\.S\.|S\.M\.S\.|SMS)\s*", "", base)
        return f"SMS {base}", base
    if folder == "Ortschaften":
        p = geo.name_parts(name)
        return p[0], p[0]
    base = re.split(r"\s[-–]\s|,", name)[0].strip()
    return name.strip(), base


def phrase_hits(q: str) -> dict:
    res = kpa.search(f'"{q}"', per_page=1, facet_by="dataProvider", max_facet_values=3)
    provs = (
        [f"{c['value']} ({c['count']})" for c in res["facet_counts"][0]["counts"]]
        if res.get("facet_counts")
        else []
    )
    docs = kpa.docs(res)
    ex = docs[0] if docs else {}
    return {
        "found": res["found"],
        "providers": "; ".join(provs),
        "example": (ex.get("title") or "")[:80],
        "url": ex.get("url", ""),
    }


def main(argv: list[str]) -> int:
    vault = Path(argv[0]) if argv else VAULT
    rows = []
    for folder in FOLDERS:
        for note in sorted((vault / folder).glob("*.md")):
            if note.stem.startswith("0_Muster"):
                continue
            strict, loose = queries(folder, note.stem)
            s = phrase_hits(strict)
            lo = phrase_hits(loose) if loose != strict else s
            status = (
                "absent"
                if s["found"] == 0 and lo["found"] == 0
                else "present_strict"
                if s["found"]
                else "loose_only"
            )
            rows.append(
                {
                    "folder": folder,
                    "note": note.stem,
                    "status": status,
                    "strict_query": strict,
                    "strict_found": s["found"],
                    "loose_query": loose,
                    "loose_found": lo["found"],
                    "top_providers": s["providers"] or lo["providers"],
                    "example": s["example"] or lo["example"],
                    "example_url": s["url"] or lo["url"],
                }
            )
    out = Path("analysis/vault_vs_kulturpool.csv")
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{'folder':<36} {'notes':>5} {'absent':>7} {'loose':>6} {'strict':>7}")
    for folder in FOLDERS:
        c = collections.Counter(r["status"] for r in rows if r["folder"] == folder)
        n = sum(c.values())
        print(f"{folder:<36} {n:>5} {c['absent']:>7} {c['loose_only']:>6} {c['present_strict']:>7}")
    c = collections.Counter(r["status"] for r in rows)
    print(
        f"{'ALL':<36} {len(rows):>5} {c['absent']:>7} {c['loose_only']:>6} {c['present_strict']:>7}"
    )
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
