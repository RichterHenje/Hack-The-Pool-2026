# Enrichment: Franz Ferdinand's hunts, 1892/93 — reception in ANNO and Kulturpool

Pipeline (Python ≥ 3.10, standard library only; API responses are cached in `.cache/`):

```bash
python3 01_extract_hunts.py   # diary OCR → data/hunt_entries.json, data/hunts.json
python3 02_anno.py            # ANNO newspapers → data/anno.json
python3 03_kulturpool.py      # Kulturpool objects → data/kulturpool.json
python3 03b_hoefer_photos.py  # Höfer itinerary + Weltmuseum/Commons photos → data/hoefer_photos.json
python3 04_build.py           # merge → data/enrichment.json, data/hunts.geojson
python3 05_export_presse.py   # ANNO clippings → ../kaiserin_elisabeth/prototype/data/presse_anno.csv
```

After step 5 rebuild the prototype bundle in `../kaiserin_elisabeth/`: `uv run python -m scripts.ke_diary`.
`reise.html` then shows each clipping on the diary day it reports on (`event_date`), not on its publication date.

**For the web app use `data/enrichment.json`** (or `data/hunts.geojson` for the map layer).

## Data model (`enrichment.json`)

```
episodes[]                       one hunting episode = consecutive diary entries in one region
  id, region, start, end         e.g. hunt-1893-03-10-nepal, 1893-03-10 … 1893-03-26
  places[]                       id, label, lat, lon, wikidata, coord_note (approximate coords flagged),
                                 vault[{note, id}] (YAML id of the vault place note, e.g. ke-place-…)
  animals[]                      id, label_de, label_en, mentions (in diary kill-sentences)
  diary                          entries[{date, band, scan}], kill_sentences, quotes[{text, animals, first_person, date, band, scan}]
  anno                           window, queries{near, issue}, issues_found, issues_high,
                                 articles[{docId, title, date, newspaper, url, thumbnail, relevance, match, snippets[{text, image, url, page}]}]
  kulturpool                     direct[] (refers to the voyage), context[] (objects about the region, NOT about FF)
  hoefer                         stays[{stay, from, to, section}], from, to, days_without_hunting_entry, diary_within_hoefer
  photos[]                       source (Weltmuseum Wien | Wikimedia Commons), title, date, url, vf_id, image, rights
voyage
  kulturpool[]                   voyage-level objects (tier: voyage | modern)
  anno_coverage                  issues per month mentioning FF / FF + hunting, 12/1892–12/1893
  anno_topics[]                  "trophies" (1893–94), "diary" (reviews of the printed diary 1895–98)
```

Join to the normalised stops via `places[].wikidata` or `diary.entries[].date` (same dates as `Sources/ff_tagebuch_eintraege.csv`).

## Method and caveats

- **Hunts** come from keyword rules (aligned with `kaiserin_elisabeth/scripts/ke_diary.py`: bare "Strecke" usually means distance in the diary, so only "zur Strecke" counts) on the *uncorrected OCR* of the printed diary: a sentence with a killing verb (erlegen, schießen, zur Strecke, Beute …) and an animal from `animals.json`. `first_person` marks sentences with *ich/mir/mein* (FF himself rather than his companions). Counts are mentions, not the number of animals killed. Known noise: "Bär" in NSW is the koala ("Australischer Bär"); elephants are often ridden, not shot (partially filtered).
- **Episodes** are grouped by `places.json` → `region`; only episodes with ≥4 kill sentences and ≥2 non-bird mentions are enriched.
- **ANNO** (`https://anno.onb.ac.at/anno-suche/rest/search/…`, see the ÖNB Labs anno-notebook): window = first hunting day … last + 70 days. `near` = proximity query `"Erzherzog Tiger"~25` (precise); `issue` = `(Erzherzog OR Thronfolger) AND (place) AND (animal OR Jagd)` anywhere in the issue (broad). `relevance: high` = a snippet names the archduke and contains a query term; `medium` = proximity hit only. Snippet text is OCR and uncorrected.
- **Kulturpool** has little on the hunts themselves. `direct` objects (NHM Intendanzakten on the museum zoologist Ludwig Lorenz von Liburnau, who travelled with FF; the ÖNB guide to the voyage collections, 1894; the 2010 exhibition "Imperial Sightseeing") are found by seed searches + one hop of `/v2/similar?on=metadata`, then filtered by voyage-specific wording and year (1892–1899, or ≥1990 as `modern`). `context` objects only share a place name.
- **Höfer itinerary** (`../Analysen/itinerary_1892_93.csv`, Höfer 2010): stays whose name matches the episode's diary spellings and that overlap the episode ±7 days. The Höfer span is often longer than the diary's hunting days (Nepal: 8–27 March vs. 10–26 March); all 20 regional episodes fall inside a Höfer stay.
- **Photos**: Weltmuseum Wien photos from `../Analysen/vf_weltmuseum.csv` (VF numbers printed by Höfer, matched by the team; only `verified`/`variants_only` with a day date) and public-domain photos from the Wikimedia Commons API, linked by date to the episode's Höfer span. Weltmuseum pages state no licence, so only the link is kept. The 24 VF numbers marked `not_online` are not on the Weltmuseum site; Europeana has no Weltmuseum records and Kulturpool has none of these photos (checked 27.10.2026).
- **Vault ids** come from the YAML properties the vault cleaner added; `places.json` stores the note titles, ids are read at build time.
- Place coordinates come from Wikidata (P625); Nepal camps, Tjipandak, Badgery Station and Aru are approximate (`coord_note`).
