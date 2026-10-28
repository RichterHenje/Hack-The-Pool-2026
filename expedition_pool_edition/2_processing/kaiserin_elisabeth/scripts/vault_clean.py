"""Vault cleaner: mechanical, source-checkable fixes plus review flags (a proposal, run on a copy).

    uv run python -m scripts.vault_clean <vault_dir> --report <report.json> [--disable R2,R3]

Rules (docs/control_battery_vault_cleaner.md):
  R1  frontmatter (type, id, created_by, checked, review) for notes without frontmatter
  R2  199x -> 189x in a Personen note when a crew-list year of that note is within ±1; else flag
  R2b year > 2026 -> its 1xxx form when another year on the same line is within 2
  R3  [[X]] without a note X: unique normalised title match -> [[Title|X]]; else flag
  R4  single-bracket [X] (also the malformed "[X])]") that matches exactly one title -> [[Title]]
  F1  possible duplicates in Personen -> review entry on each
  F2  ship/event titles in Personen, country/region titles in Ortschaften -> review entry
Files are read and written as bytes: BOM and line endings are kept; only changed files are
written. Templates (0_Muster*) and .obsidian/.trash are never touched. The report lists every
change (file, rule, before, after) and every flag; files not in it are unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from kp.geo import COUNTRIES

TYPES = {
    "Personen": "person",
    "Ortschaften": "place",
    "Schiffe": "ship",
    "Firmen_Dienstleister_Institutionen": "organisation",
    "Sammlungen_Projekte": "collection",
}
ROLE_WORDS = {
    "dr",
    "prof",
    "graf",
    "gf",
    "freiherr",
    "frhr",
    "ritter",
    "ritt",
    "von",
    "v",
    "vu",
    "z",
    "edler",
    "edl",
    "kapitan",
    "capitan",
    "kommandant",
    "commandant",
    "linienschiffs",
    "linienschiffskapitan",
    "fregattenkapitan",
    "korvettenkapitan",
    "corvettenkapitan",
    "mr",
    "captain",
    "erzherzog",
    "sir",
}
REGIONS = {
    "ostasien",
    "nordamerika",
    "levante",
    "mittelmeer",
    "borneo",
    "himalaya",
    "ozeanien und insulares sud ostasien",
    "indien british raj 1858 1947",
}
SHIP_PREFIX = re.compile(r"^(S\.?\s?M\.?\s?S\.?|H\.?\s?M\.?\s?S\.?)\s", re.IGNORECASE)
LINK = re.compile(r"\[\[([^\]\|#\n]+)((?:#[^\]\|\n]*)?)(\|[^\]\n]*)?\]\]")
SINGLE_MALFORMED = re.compile(r"(?<!\[)\[([^\[\]\n]{2,80})\]\)\]")
SINGLE = re.compile(r"(?<![\[\]!])\[([^\[\]\n]{2,80})\](?![\]\(\[:])")
YEAR_199 = re.compile(r"\b199\d\b")
YEAR_FUTURE = re.compile(r"\b(2(?:0[3-9]\d|[1-9]\d\d))\b")
YEAR_ANY = re.compile(r"\b(1[5-9]\d\d)\b")
LIST_YEAR = re.compile(r"RangUndEinteilungslisteMarine_(\d{4})|Rangliste (\d{4})")
URL = re.compile(r"https?://\S+")


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.casefold().replace("ß", "ss"))
    return "".join(c for c in s if not unicodedata.combining(c))


def tokens(title: str) -> list[str]:
    return [t for t in re.split(r"[^\w]+", fold(title)) if t and t not in ROLE_WORDS]


def key(title: str) -> str:
    return " ".join(sorted(tokens(title)))


def lev1(a: str, b: str) -> bool:
    """Edit distance exactly 1 (one substitution, insertion or deletion)."""
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    s, t = (a, b) if len(a) < len(b) else (b, a)
    return any(s == t[:i] + t[i + 1 :] for i in range(len(t)))


class Note:
    def __init__(self, path: Path, vault: Path):
        self.path, self.rel = path, path.relative_to(vault).as_posix()
        self.folder = path.parent.name if path.parent != vault else ""
        self.title = unicodedata.normalize("NFC", path.stem)
        raw = path.read_bytes()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        self.text = raw.decode("utf-8-sig" if self.bom else "utf-8", errors="surrogateescape")
        self.orig = self.text
        self.eol = "\r\n" if "\r\n" in self.text else "\n"
        self.sha_before = hashlib.sha256(raw).hexdigest()

    def write(self) -> str:
        data = self.text.encode("utf-8", errors="surrogateescape")
        if self.bom:
            data = b"\xef\xbb\xbf" + data
        self.path.write_bytes(data)
        return hashlib.sha256(data).hexdigest()


def split_frontmatter(text: str, eol: str) -> tuple[str, str]:
    """('---…---<eol>', body) when the note starts with a YAML block, else ('', text)."""
    if not text.startswith("---" + eol):
        return "", text
    end = text.find(eol + "---", 3)
    if end < 0:
        return "", text
    cut = end + len(eol) + 3
    if text[cut : cut + len(eol)] == eol:
        cut += len(eol)
    return text[:cut], text[cut:]


def load(vault: Path) -> list[Note]:
    out = []
    for p in sorted(vault.rglob("*.md")):
        parts = set(p.relative_to(vault).parts)
        if ".obsidian" in parts or ".trash" in parts or p.stem.startswith("0_Muster"):
            continue
        out.append(Note(p, vault))
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault", type=Path)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--disable", default="")
    a = ap.parse_args(argv)
    off = {r.strip().upper() for r in a.disable.split(",") if r.strip()}
    notes = load(a.vault)
    titles = {n.title for n in notes}
    by_key = defaultdict(list)
    for t in titles:
        by_key[key(t)].append(t)
    changes, flags = [], defaultdict(list)

    def change(n: Note, rule: str, before: str, after: str) -> None:
        changes.append({"file": n.rel, "rule": rule, "before": before, "after": after})

    for n in notes:
        # Rules read the body only: a review entry in existing frontmatter ("Link ohne Ziel",
        # "Jahreszahl prüfen: 1992") must not be read as note text again (real run, 2nd pass).
        fm, n.text = split_frontmatter(n.text, n.eol)
        # R3 broken links with a unique normalised target
        if "R3" not in off:

            def fix_link(m: re.Match, n: Note = n) -> str:
                target = unicodedata.normalize("NFC", m.group(1).strip())
                if target in titles:
                    return m.group(0)
                cands = by_key.get(key(target), [])
                if len(cands) == 1 and key(target):
                    alias = m.group(3) or f"|{m.group(1)}"
                    new = f"[[{cands[0]}{m.group(2)}{alias}]]"
                    change(n, "R3", m.group(0), new)
                    return new
                # no brackets: in frontmatter Obsidian would read [[…]] as a real (broken) link
                flags[n.rel].append(("R3", f"Link ohne Ziel: {target}"))
                return m.group(0)

            n.text = LINK.sub(fix_link, n.text)
        # R4 single-bracket links (malformed first)
        if "R4" not in off:

            def fix_single(m: re.Match, n: Note = n, malformed: bool = False) -> str:
                inner = m.group(1) + (")" if malformed else "")
                cands = by_key.get(key(inner), []) if key(inner) else []
                if inner.strip() in titles:
                    cands = [inner.strip()]
                if len(cands) == 1:
                    new = f"[[{cands[0]}]]"
                    change(n, "R4", m.group(0), new)
                    return new
                return m.group(0)

            n.text = SINGLE_MALFORMED.sub(lambda m: fix_single(m, malformed=True), n.text)
            n.text = SINGLE.sub(fix_single, n.text)
        # R2 date slips in Personen notes
        if n.folder == "Personen":
            list_years = {int(y) for m in LIST_YEAR.finditer(n.text) for y in m.groups() if y}
            url_spans = [m.span() for m in URL.finditer(n.text)]

            def fix_199(
                m: re.Match, n: Note = n, ly: set = list_years, spans: list = url_spans
            ) -> str:
                if any(s <= m.start() < e for s, e in spans):
                    return m.group(0)
                cand = int(m.group(0)) - 100
                if "R2" not in off and any(abs(cand - y) <= 1 for y in ly):
                    change(n, "R2", m.group(0), str(cand))
                    return str(cand)
                flags[n.rel].append(("R2", f"Jahreszahl prüfen: {m.group(0)}"))
                return m.group(0)

            n.text = YEAR_199.sub(fix_199, n.text)
        # R2b impossible years
        if "R2B" not in off:
            lines = n.text.split(n.eol)
            for i, line in enumerate(lines):
                for m in list(YEAR_FUTURE.finditer(line)):
                    cand = "1" + m.group(1)[1:]
                    others = [int(y) for y in YEAR_ANY.findall(line)]
                    if any(abs(int(cand) - y) <= 2 for y in others):
                        new_line = line[: m.start()] + cand + line[m.end() :]
                        change(n, "R2b", line.strip(), new_line.strip())
                        line = new_line
                lines[i] = line
            n.text = n.eol.join(lines)
        n.text = fm + n.text

    # F1 duplicates in Personen
    persons = [n for n in notes if n.folder == "Personen"]
    if "F1" not in off:
        groups = defaultdict(list)
        for n in persons:
            groups[key(n.title)].append(n)
        for g in groups.values():
            if len(g) > 1:
                for n in g:
                    others = ", ".join(f"[[{o.title}]]" for o in g if o is not n)
                    flags[n.rel].append(("F1", f"Dublette? {others}"))
        comma = [(n, *map(str.strip, n.title.split(",", 1))) for n in persons if "," in n.title]
        for i, (n1, last1, first1) in enumerate(comma):
            for n2, last2, first2 in comma[i + 1 :]:
                if (
                    key(first1)
                    and key(first1) == key(first2)
                    and len(last1) >= 4
                    and lev1(fold(last1), fold(last2))
                ):
                    flags[n1.rel].append(("F1", f"Dublette? [[{n2.title}]]"))
                    flags[n2.rel].append(("F1", f"Dublette? [[{n1.title}]]"))
        # Titles with a role word and no "Last, First" comma ("Kapitän Franz Mirtl") against other
        # such titles only. Comma titles are excluded: there "Ritter" can be a surname
        # (loop 1 false positive: "Ritter, Franz von" vs the world-tour note).
        role = [
            n
            for n in persons
            if "," not in n.title and set(re.split(r"[^\w]+", fold(n.title))) & ROLE_WORDS
        ]
        for n1 in role:
            t1 = set(tokens(n1.title))
            for n2 in role:
                t2 = set(tokens(n2.title))
                if n2 is not n1 and t1 and t2 and t1 < t2 and any(len(t) >= 4 for t in t1):
                    flags[n1.rel].append(("F1", f"Dublette? [[{n2.title}]]"))
                    flags[n2.rel].append(("F1", f"Dublette? [[{n1.title}]]"))
    # F2 misfiled types
    if "F2" not in off:
        for n in notes:
            if n.folder == "Personen" and (
                SHIP_PREFIX.match(n.title) or re.search(r"weltreise|eskader", fold(n.title))
            ):
                flags[n.rel].append(("F2", "Typ prüfen: Schiff oder Ereignis unter Personen"))
            if n.folder == "Ortschaften":
                k = re.sub(r"[^\w]+", " ", fold(n.title)).strip()
                # city-states are places (loop 1 false positive: Singapur)
                if k in REGIONS or (k in COUNTRIES and COUNTRIES[k] not in {"SG", "HK", "MO"}):
                    flags[n.rel].append(("F2", "Typ prüfen: Land oder Region, kein Ort"))

    # R1 frontmatter (and review entries)
    for n in notes:
        review = sorted({msg for _, msg in flags.get(n.rel, [])})
        has_fm = n.text.startswith("---" + n.eol) or n.text.startswith("---\n")
        if not has_fm and "R1" not in off:
            typ = TYPES.get(n.folder, "note")
            ident = "ke-" + typ + "-" + hashlib.sha1(n.rel.encode()).hexdigest()[:10]
            made = "ai-assisted" if "RangUndEinteilungslisteMarine_" in n.text else "human"
            lines = ["---", f"type: {typ}", f"id: {ident}", f"created_by: {made}", "checked: false"]
            if review:
                lines.append("review:")
                lines += ["  - " + json.dumps(r, ensure_ascii=False) for r in review]
            lines.append("---")
            block = n.eol.join(lines) + n.eol
            n.text = block + n.text
            change(n, "R1", "", f"frontmatter ({typ}, {made}, {len(review)} review)")
        elif has_fm and review and "review:" not in n.text.split("---", 2)[1]:
            end = n.text.index("---", 3)
            ins = (
                "review:"
                + n.eol
                + n.eol.join("  - " + json.dumps(r, ensure_ascii=False) for r in review)
                + n.eol
            )
            n.text = n.text[:end] + ins + n.text[end:]
            change(n, "R1", "", f"review in existing frontmatter ({len(review)})")

    written = {}
    for n in notes:
        if n.text != n.orig:
            written[n.rel] = {"sha256_before": n.sha_before, "sha256_after": n.write()}
    report = {
        "vault": str(a.vault),
        "disabled": sorted(off),
        "notes": len(notes),
        "changed_files": written,
        "changes": changes,
        "flags": {f: [{"rule": r, "message": m} for r, m in v] for f, v in flags.items()},
    }
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    per = defaultdict(int)
    for c in changes:
        per[c["rule"]] += 1
    fl = defaultdict(int)
    for v in flags.values():
        for r, _ in v:
            fl[r] += 1
    print(
        f"{len(notes)} notes; changed files {len(written)}; changes {dict(per)}; flags {dict(fl)}"
    )
    print(f"-> {a.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
