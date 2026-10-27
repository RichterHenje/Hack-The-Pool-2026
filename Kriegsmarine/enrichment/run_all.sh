#!/usr/bin/env bash
# Rebuild the enrichment from the normalised data (../normalization/json). API responses are cached
# in .cache/, so a second run works offline. Step 5 writes into the prototype; rebuild its bundle
# afterwards in ../kaiserin_elisabeth with: uv run python -m scripts.ke_diary
set -euo pipefail
cd "$(dirname "$0")"
for step in 00_places 01_extract_hunts 02_anno 03_kulturpool 03b_hoefer_photos 03c_people 03d_objects 04_build \
            05_export_presse 06_crosscheck_ffworld 07_heroes; do
  echo "== $step"
  python3 "$step.py"
done
