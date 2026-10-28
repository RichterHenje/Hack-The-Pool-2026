"""One blind loop for the vault cleaner: disable-rule checks, full run, idempotence, scoring.

    uv run python -m scripts.vault_clean_loop <loop_dir>

<loop_dir> holds `vault/` (planted by a separate agent) and `manifest.json` (its answers).
This script is written before the manifest is read; it is the only reader of the manifest.
Steps:
  1. copy vault -> pristine/ (the planted state, kept)
  2. per rule R2, R2b, R3, R4, F1, F2: copy pristine -> off_<rule>/, clean with that rule
     disabled, score: the rule's plant class must come out MISSED (the scorer can fail)
  3. clean vault/ with all rules, score
  4. clean vault/ again: must change nothing (idempotence)
Writes <loop_dir>/score.json and score.md. Nothing is deleted.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

from scripts import vault_clean

CLASS_RULE = {"P1": "R2", "P2": "R2B", "P3": "R3", "P5": "R4", "P6": "F1", "P7": "F2"}


def clean(vault: Path, report: Path, disable: str = "") -> dict:
    args = [str(vault), "--report", str(report)] + (["--disable", disable] if disable else [])
    vault_clean.main(args)
    return json.loads(report.read_text(encoding="utf-8"))


def score(vault: Path, report: dict, manifest: dict) -> dict:
    res = defaultdict(lambda: {"n": 0, "ok": 0, "misses": []})
    flags = report["flags"]
    for p in manifest["plants"]:
        f = vault / p["file"]
        text = f.read_text(encoding="utf-8-sig") if f.exists() else ""
        cls, expect = p["class"], p["expect"]
        if expect == "fix":
            ok = p["expected"] in text and p["planted"] not in text
        elif expect == "unchanged":
            ok = p["planted"] in text
        elif expect == "flag":
            rule = "F1" if cls == "P6" else "F2"
            files = [p["file"]] + ([p["related_file"]] if p.get("related_file") else [])
            ok = all(any(x["rule"] == rule for x in flags.get(fl, [])) for fl in files)
        elif expect == "identical":
            ok = hashlib.sha256(f.read_bytes()).hexdigest() == p["sha256_after_plant"]
        else:
            ok = False
        r = res[cls]
        r["n"] += 1
        r["ok"] += ok
        if not ok:
            r["misses"].append(p["id"])
    # P4 also needs the broken link flagged
    for p in manifest["plants"]:
        if p["class"] == "P4" and not any(x["rule"] == "R3" for x in flags.get(p["file"], [])):
            res["P4"]["misses"].append(p["id"] + ":not-flagged")
    plant_files = {p["file"] for p in manifest["plants"]} | {
        p["related_file"] for p in manifest["plants"] if p.get("related_file")
    }
    planted_in = defaultdict(list)
    for p in manifest["plants"]:
        if p.get("planted"):
            planted_in[p["file"]].append(p["planted"])

    def explained(c: dict) -> bool:
        # an edit in a planted file counts as the plant's only if it touches the planted text
        # (after loop 1/2: real fixes inside planted files were hidden from this list)
        return c["file"] in plant_files and any(
            c["before"] and (c["before"] in s or s in c["before"]) for s in planted_in[c["file"]]
        )

    outside = [c for c in report["changes"] if c["rule"] != "R1" and not explained(c)]
    return {"classes": dict(res), "edits_outside_plants": outside}


def main(argv: list[str]) -> int:
    loop = Path(argv[0])
    manifest = json.loads((loop / "manifest.json").read_text(encoding="utf-8"))
    pristine = loop / "pristine"
    if not pristine.exists():
        shutil.copytree(loop / "vault", pristine)
    out = {"seed": manifest.get("seed"), "disable_checks": {}}
    for cls, rule in CLASS_RULE.items():
        d = loop / f"off_{rule}"
        if not d.exists():
            shutil.copytree(pristine, d)
        rep = clean(d, loop / f"report_off_{rule}.json", rule)
        s = score(d, rep, manifest)["classes"].get(cls, {"n": 0, "ok": 0})
        out["disable_checks"][rule] = {
            "class": cls,
            "n": s["n"],
            "ok_when_disabled": s["ok"],
            "scorer_can_fail": s["n"] > 0 and s["ok"] < s["n"],
        }
    rep = clean(loop / "vault", loop / "report.json")
    out["full"] = score(loop / "vault", rep, manifest)
    rep2 = clean(loop / "vault", loop / "report_second_run.json")
    out["idempotent"] = rep2["changed_files"] == {}
    out["changed_files"] = len(rep["changed_files"])
    (loop / "score.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    lines = [
        f"# Blind loop {loop.name} (seed {out['seed']})",
        "",
        "| class | caught | of | misses |",
        "| --- | ---: | ---: | --- |",
    ]
    for cls in sorted(out["full"]["classes"]):
        c = out["full"]["classes"][cls]
        lines.append(f"| {cls} | {c['ok']} | {c['n']} | {', '.join(c['misses']) or '–'} |")
    lines += [
        "",
        "| rule disabled | class | caught while disabled | scorer can fail |",
        "| --- | --- | ---: | --- |",
    ]
    for rule, d in out["disable_checks"].items():
        lines.append(
            f"| {rule} | {d['class']} | {d['ok_when_disabled']} of {d['n']} | {d['scorer_can_fail']} |"
        )
    lines += [
        "",
        f"Idempotent (second run changes nothing): {out['idempotent']}",
        f"Changed files: {out['changed_files']}",
        f"Edits outside plants (must map to real issues): {len(out['full']['edits_outside_plants'])}",
    ]
    for c in out["full"]["edits_outside_plants"]:
        lines.append(f"- {c['rule']} {c['file']}: {c['before'][:80]!r} -> {c['after'][:80]!r}")
    (loop / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
