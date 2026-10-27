"""Quality review of the team's Obsidian vault (rerun after every import).

    uv run python -m scripts.vault_review [vault_dir]

Writes analysis/vault_review.md: inventory, template field fill rates per folder,
identifiers, sources, link graph (broken links, orphans, hubs), implausible years,
and near-duplicate names. Read-only on the vault. Findings are candidates for a
human to check, not corrections.
"""

from __future__ import annotations

import collections
import difflib
import re
import sys
from pathlib import Path

from kp import geo
from scripts.vault_places import VAULT, wikilinks

FOLDERS = [
    "Personen",
    "Firmen_Dienstleister_Institutionen",
    "Schiffe",
    "Sammlungen_Projekte",
    "Ortschaften",
]
FIELD = re.compile(r"^\s*-\s+([^:\n]+?)\s*(?::\s*(.*))?$")
YEAR = re.compile(r"\b(1[5-9]\d\d|2\d\d\d)\b")
PLAUSIBLE = (1800, 1945)  # voyages 1880s-1910s; biographies may run wider


def template_fields(path: Path) -> list[str]:
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = FIELD.match(line)
        if m and not line.startswith(("\t", "    ")):
            out.append(re.sub(r"\s*\(.*\)$", "", m.group(1)).strip())
    return out


def filled(text: str, field: str) -> bool:
    """A field counts as filled if its line has a value after ':' (or a link) or an
    indented sub-bullet with a value follows it."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = FIELD.match(line)
        if not m or line.startswith(("\t", "    ")):
            continue
        name = re.sub(r"\s*\(.*\)$", "", m.group(1)).strip()
        if name != field:
            continue
        if (m.group(2) or "").strip() or "[[" in m.group(1) or "http" in m.group(1):
            return True
        for sub in lines[i + 1 :]:
            if not sub.startswith(("\t", "    ")):
                break
            sm = FIELD.match(sub)
            if sm and (sm.group(2) or "").strip():
                return True
        return False
    return False


def main(argv: list[str]) -> int:
    vault = Path(argv[0]) if argv else VAULT
    notes = {p.stem: p for p in vault.rglob("*.md") if ".trash" not in p.parts}
    texts = {k: p.read_text(encoding="utf-8", errors="replace") for k, p in notes.items()}
    out = ["# Vault review", "", f"Vault: `{vault.as_posix()}`", ""]

    # Inventory
    out += ["## Inventory", "", "| folder | notes |", "| --- | ---: |"]
    for f in FOLDERS:
        n = len([p for p in (vault / f).glob("*.md") if not p.stem.startswith("0_Muster")])
        out.append(f"| {f} | {n} |")
    root = [p.name for p in vault.iterdir() if p.is_file()]
    out += ["", f"Root files: {', '.join(sorted(root))}", ""]

    # Field fill rates
    out += ["## Template fields filled (share of notes)", ""]
    for f in FOLDERS:
        tpl = next((vault / f).glob("0_Muster*.md"), None)
        if not tpl:
            continue
        fields = template_fields(tpl)
        ns = [p for p in (vault / f).glob("*.md") if not p.stem.startswith("0_Muster")]
        if not ns:
            continue
        uses = sum(
            sum(
                bool(FIELD.match(ln))
                and re.sub(r"\s*\(.*\)$", "", FIELD.match(ln).group(1)).strip() in fields
                for ln in texts[p.stem].splitlines()
            )
            >= 2
            for p in ns
        )
        out += [
            f"**{f}** ({len(ns)} notes; {uses} use the template bullets, the rest are free text)",
            "",
            "| field | filled |",
            "| --- | ---: |",
        ]
        for fld in fields:
            k = sum(filled(texts[p.stem], fld) for p in ns)
            out.append(f"| {fld} | {k} ({k / len(ns):.0%}) |")
        out.append("")

    # Identifiers and sources
    ids = collections.Counter()
    for t in texts.values():
        ids["GND (d-nb.info)"] += bool(re.search(r"d-nb\.info/gnd", t))
        ids["VIAF"] += bool(re.search(r"viaf\.org", t, re.IGNORECASE))
        ids["Wikidata"] += bool(re.search(r"wikidata\.org", t, re.IGNORECASE))
        ids["GeoNames"] += bool(re.search(r"geonames\.org/\d", t, re.IGNORECASE))
        ids["Hungaricana source link"] += "hungaricana.hu" in t
        ids["PDF filename as source"] += bool(re.search(r"\.pdf\b", t))
        ids["Goobi link"] += bool(re.search(r"goobi", t, re.IGNORECASE) and "http" in t)
    out += [
        "## Identifiers and sources (notes containing)",
        "",
        "| kind | notes |",
        "| --- | ---: |",
    ]
    out += [f"| {k} | {v} |" for k, v in ids.items()] + [""]

    # Link graph
    titles = set(notes)
    inbound = collections.Counter()
    broken = collections.Counter()
    outdeg = {}
    for k, t in texts.items():
        ls = set(wikilinks(t)) - {k}
        outdeg[k] = len(ls)
        for target in ls:
            if target in titles:
                inbound[target] += 1
            else:
                broken[target] += 1
    orphans = [
        k
        for k in notes
        if not inbound[k]
        and not outdeg[k]
        and not k.startswith("0_Muster")
        and notes[k].parent.name in FOLDERS
    ]
    out += [
        "## Link graph",
        "",
        f"- links: {sum(outdeg.values())}; notes with no link in or out: **{len(orphans)}**",
        f"- broken link targets (no note with that title): **{len(broken)}**",
        "",
        "Most linked: " + "; ".join(f"{k} ({v})" for k, v in inbound.most_common(8)),
        "",
        "Broken targets (most used first): "
        + "; ".join(f"{k} ({v})" for k, v in broken.most_common(15)),
        "",
        "Orphans by folder: "
        + "; ".join(f"{f} {sum(notes[o].parent.name == f for o in orphans)}" for f in FOLDERS),
        "",
    ]

    # Implausible years. Impossible anywhere: after 2026. Implausible in crew and voyage
    # notes (service 1870s-1918): after PLAUSIBLE[1]. Place notes legitimately cite 1947/48.
    odd = []
    for k, t in texts.items():
        folder = notes[k].parent.name
        if k.startswith("0_Muster") or folder not in FOLDERS:
            continue
        for y in {int(y) for y in YEAR.findall(re.sub(r"https?://\S+", "", t))}:
            if y > 2026 or (folder in ("Personen", "Schiffe") and y > PLAUSIBLE[1]):
                odd.append((folder, k, y))
    out += [
        "## Likely date slips",
        "",
        (
            f"{len(odd)} years in {len({k for _, k, _ in odd})} notes: after 2026, or after "
            f"{PLAUSIBLE[1]} in a person or ship note (e.g. 1994 for 1894). Check against the source."
        ),
        "",
    ]
    out += [f"- {f}/{k}: {y}" for f, k, y in sorted(odd)] + [""]

    # Near-duplicate names within each folder
    out += ["## Near-duplicate titles (same folder, similarity ≥ 0.88)", ""]
    for f in FOLDERS:
        names = sorted(p.stem for p in (vault / f).glob("*.md") if not p.stem.startswith("0_"))
        keys = {n: geo.norm(n) for n in names}
        pairs = []
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                if keys[a][:2] != keys[b][:2]:
                    continue
                r = difflib.SequenceMatcher(None, keys[a], keys[b]).ratio()
                if r >= 0.88:
                    pairs.append((a, b, r))
        if pairs:
            out.append(f"**{f}**: " + "; ".join(f"{a} ↔ {b} ({r:.2f})" for a, b, r in pairs))
            out.append("")

    path = Path("analysis/vault_review.md")
    path.parent.mkdir(exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:60]))
    print(f"... -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
