#!/usr/bin/env bash
# Needs EUROPEANA_API_KEY in the environment or in the repo's .env (step 03e).
# Rebuild the enrichment from the normalised data (../normalization/json). API responses are cached
# in .cache/, so a second run works offline. Step 5 writes into the prototype; rebuild its bundle
# afterwards in ../kaiserin_elisabeth with: uv run python -m scripts.ke_diary
# Step 8 bundles everything for prototype/reise.html (data/ke_enrichment.js).
set -euo pipefail
cd "$(dirname "$0")"
for step in 00_places 01_extract_hunts 02_anno 03_kulturpool 03b_hoefer_photos 03c_people 03d_objects 03e_europeana 03f_person_sources 04_build \
            05_export_presse 06_crosscheck_ffworld 07_heroes 08_export_prototype; do
  echo "== $step"
  python3 "$step.py"
done
