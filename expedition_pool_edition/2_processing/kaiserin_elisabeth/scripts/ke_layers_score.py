"""Blind test of the layer joins (docs/control_battery_layers.md).

    uv run python -m scripts.ke_layers_score <loop_dir>

<loop_dir> holds vault/, sources/ (planted by a separate agent) and manifest.json. Runs
scripts.ke_layers with all joins and with each join disabled, scores the plants:
  A1/A2 aboard days == expected_days; L1/L2 actor days == expected_days;
  C1 sentence extracted on its day; C2 not extracted.
Writes <loop_dir>/score.md. Read-only on the plants.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from scripts import ke_layers

CLASS_JOIN = {"A1": "J1", "L1": "J2", "C1": "J3"}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def run(loop: Path, disable: str = "") -> dict:
    out = loop / f"layers{'_off_' + disable if disable else ''}.json"
    args = ["--vault", str(loop / "vault"), "--sources", str(loop / "sources"), "--out", str(out)]
    ke_layers.main(args + (["--disable", disable] if disable else []))
    return json.loads(out.read_text(encoding="utf-8"))


def score(layers: dict, manifest: dict) -> dict:
    days = layers["days"]
    res = defaultdict(lambda: {"n": 0, "ok": 0, "misses": []})
    for p in manifest["plants"]:
        cls = p["class"]
        if cls in ("A1", "A2"):
            got = sorted(
                d
                for d, e in days.items()
                if any(a["name"] == p["name"] for a in e.get("aboard", []))
            )
            ok = got == sorted(p["expected_days"])
        elif cls in ("L1", "L2"):
            got = sorted(
                d
                for d, e in days.items()
                if any(a["note"] == p["name"] for a in e.get("actors", []))
            )
            ok = got == sorted(p["expected_days"])
        elif cls in ("C1", "C2"):
            want = norm(p["sentence"])[:60]
            found = any(want in norm(s) for s in days.get(p["date"], {}).get("collecting", []))
            ok = found if cls == "C1" else not found
        else:
            ok = False
        r = res[cls]
        r["n"] += 1
        r["ok"] += ok
        if not ok:
            r["misses"].append(p["id"])
    return dict(res)


def main(argv: list[str]) -> int:
    loop = Path(argv[0])
    manifest = json.loads((loop / "manifest.json").read_text(encoding="utf-8"))
    full = score(run(loop), manifest)
    lines = [
        f"# Layer joins, blind loop {loop.name} (seed {manifest.get('seed')})",
        "",
        "| class | ok | of | misses |",
        "| --- | ---: | ---: | --- |",
    ]
    lines += [
        f"| {c} | {v['ok']} | {v['n']} | {', '.join(v['misses']) or '–'} |"
        for c, v in sorted(full.items())
    ]
    lines += [
        "",
        "| join disabled | class | ok while disabled | scorer can fail |",
        "| --- | --- | ---: | --- |",
    ]
    for cls, join in CLASS_JOIN.items():
        s = score(run(loop, join), manifest).get(cls, {"n": 0, "ok": 0})
        lines.append(
            f"| {join} | {cls} | {s['ok']} of {s['n']} | {s['n'] > 0 and s['ok'] < s['n']} |"
        )
    (loop / "score.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
