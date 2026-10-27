# Enrichment: Franz Ferdinand's hunts, 1892/93 — reception in ANNO and Kulturpool

Builds on the normalised data in `../normalization/json/` (vault → `filter_voyage.py`, diary → `diary_days.py`)
and adds external sources: Wikidata, ANNO, Kulturpool, Höfer's itinerary, Weltmuseum/Commons photos,
franzferdinandsworld.com. Python ≥ 3.10, standard library only; API responses are cached in `.cache/`.

```bash
./run_all.sh                  # all steps in order
python3 00_places.py          # normalised route places + Wikidata → data/route_places.json, route.geojson, places_resolved.json
python3 01_extract_hunts.py   # diary days (normalization) → data/hunt_entries.json, data/hunts.json
python3 02_anno.py            # ANNO newspapers → data/anno.json
python3 03_kulturpool.py      # Kulturpool objects → data/kulturpool.json
python3 03b_hoefer_photos.py  # Höfer itinerary + Weltmuseum/Commons photos → data/hoefer_photos.json
python3 03c_people.py         # people of the voyage: diary, hunts, GND/Wikidata, ANNO, Kulturpool → data/people.json
python3 04_build.py           # merge → data/enrichment.json, data/hunts.geojson
python3 05_export_presse.py   # ANNO clippings → ../kaiserin_elisabeth/prototype/data/presse_anno.csv
python3 06_crosscheck_ffworld.py  # itinerary check vs franzferdinandsworld.com → data/ffworld_days.csv, ffworld_crosscheck.json
python3 07_heroes.py          # surviving animals (heroes.json, curated) → data/heroes.json, heroes.geojson
```

After step 5 rebuild the prototype bundle in `../kaiserin_elisabeth/`: `uv run python -m scripts.ke_diary`.
`reise.html` then shows each clipping on the diary day it reports on (`event_date`), not on its publication date.

Hand-maintained inputs: `places.json` (hunting places: OCR/day spellings, ANNO terms, region, vault notes),
`route_wikidata.json` (QID per route place), `animals.json`, `heroes.json`.

**For the web app use `data/enrichment.json`** (or `data/hunts.geojson` for the map layer).

## Data model (`enrichment.json`)

```
episodes[]                       one hunting episode = consecutive diary entries in one region
  id, region, start, end         e.g. hunt-1893-03-10-nepal, 1893-03-10 … 1893-03-26
  places[]                       id, label, lat, lon (from Wikidata), wikidata, coord_note (approximate coords flagged),
                                 vault[{note, id}] (vault place note + id from normalization/json/ortschaften.json), on_route
  animals[]                      id, label_de, label_en, mentions (in diary kill-sentences)
  diary                          entries[{date, band, scan}], kill_sentences, quotes[{text, animals, first_person, date, band, scan}]
  anno                           window, queries{near, issue}, issues_found, issues_high,
                                 articles[{docId, title, date, newspaper, url, thumbnail, relevance, match, snippets[{text, image, url, page}]}]
  kulturpool                     direct[] (refers to the voyage), context[] (objects about the region, NOT about FF)
  hoefer                         stays[{stay, from, to, section}], from, to, days_without_hunting_entry, diary_within_hoefer
  photos[]                       source (Weltmuseum Wien | Wikimedia Commons), title, date, url, vf_id, image, rights
  people[]                       who is named in the episode's kill sentences: id (vault), name, group, kill_sentences, gnd, wikidata
voyage
  kulturpool[]                   voyage-level objects (tier: voyage | modern)
  anno_coverage                  issues per month mentioning FF / FF + hunting, 12/1892–12/1893
  anno_topics[]                  "trophies" (1893–94), "diary" (reviews of the printed diary 1895–98)
```

Join to the normalised data via `places[].vault[].id` (= `_meta.id` in `normalization/json/ortschaften.json`),
`places[].wikidata`, or `diary.entries[].date` (= `date` in `normalization/json/tagebuch_tage.json`).
The whole route with coordinates is in `data/route_places.json` / `data/route.geojson`.

## Method and caveats

- **Hunts** come from keyword rules (aligned with `kaiserin_elisabeth/scripts/ke_diary.py`: bare "Strecke" usually means distance in the diary, so only "zur Strecke" counts) on the *uncorrected OCR* of the printed diary: a sentence with a killing verb (erlegen, schießen, zur Strecke, Beute …) and an animal from `animals.json`. `first_person` marks sentences with *ich/mir/mein* (FF himself rather than his companions). Counts are mentions, not the number of animals killed. Known noise: "Bär" in NSW is the koala ("Australischer Bär"); elephants are often ridden, not shot (partially filtered).
- **Episodes** are grouped by `places.json` → `region`; only episodes with ≥4 kill sentences and ≥2 non-bird mentions are enriched.
- **ANNO** (`https://anno.onb.ac.at/anno-suche/rest/search/…`, see the ÖNB Labs anno-notebook): window = first hunting day … last + 70 days. `near` = proximity query `"Erzherzog Tiger"~25` (precise); `issue` = `(Erzherzog OR Thronfolger) AND (place) AND (animal OR Jagd)` anywhere in the issue (broad). `relevance: high` = a snippet names the archduke and contains a query term; `medium` = proximity hit only. Snippet text is OCR and uncorrected.
- **Kulturpool** has little on the hunts themselves. `direct` objects (NHM Intendanzakten on the museum zoologist Ludwig Lorenz von Liburnau, who travelled with FF; the ÖNB guide to the voyage collections, 1894; the 2010 exhibition "Imperial Sightseeing") are found by seed searches + one hop of `/v2/similar?on=metadata`, then filtered by voyage-specific wording and year (1892–1899, or ≥1990 as `modern`). `context` objects only share a place name.
- **Höfer itinerary** (`../Analysen/itinerary_1892_93.csv`, Höfer 2010): stays whose name matches the episode's diary spellings and that overlap the episode ±7 days. The Höfer span is often longer than the diary's hunting days (Nepal: 8–27 March vs. 10–26 March); all 20 regional episodes fall inside a Höfer stay.
- **Photos**: Weltmuseum Wien photos from `../Analysen/vf_weltmuseum.csv` (VF numbers printed by Höfer, matched by the team; only `verified`/`variants_only` with a day date) and public-domain photos from the Wikimedia Commons API, linked by date to the episode's Höfer span. Weltmuseum pages state no licence, so only the link is kept. The 24 VF numbers marked `not_online` are not on the Weltmuseum site; Europeana has no Weltmuseum records and Kulturpool has none of these photos (checked 27.10.2026).
- **Vault ids** come from `normalization/json/ortschaften.json` (Lisa's filter of the vault); `places.json` stores the note titles. Three hunting places are not on the normalised route (Bharatpur; Banff and Penticton, travelled on another ship).
- **Heroes** (`heroes.json`, hand-curated): the live animals of the voyage – the ship's menagerie ("Bordmenagerie": monkeys Fips and Mucki, birds, a piglet, bears from Japan …) and animals sent to Vienna (Schönbrunn, the archduke's palace). Every claim cites a diary date or an ANNO issue and page; `06_heroes.py` checks each quote against its source and fails if one is not found. `status`: free / schoenbrunn / vienna / died / unknown; `evidence`: diary / press / probable (our inference, explained in `note`). ANNO's page full text sits behind a bot check, so press quotes are assembled from snippets; joins are marked with `…`.
- **Cross-check with franzferdinandsworld.com** (step 07, 27.10.2026): the site lists all 309 days (14.12.1892–18.10.1893) with a place, 284 with a page holding an English translation of that day. Against Höfer (304 days) and the diary headings (159 days) there is no contradiction: the differences are sea passages named differently, spellings/OCR, and stops on the way (Poona, Patna). Two problems on our side:
  - **The OCR diary has 170 entries, the book ~284 days.** The OCR lost many inline date headings, so 63 entries span several days. Fixed upstream: `normalization/diary_days.py` splits the diary into days, and all steps now date by day. Leander's `kaiserin_elisabeth/prototype/data/ke_diary.json` still uses the 170 entries.
  - **Pages are missing from the OCR** (e.g. 31 March, 15 July: the drowned parrot, the steamer „Vindobona“ and the 14 monkeys). Those passages are cited from the site's translation (`site` quotes, checked against the cached page).
  - Höfer's table (`../Analysen/itinerary_1892_93.csv`) has an empty stage for 1–4 January 1893.
- **People** (`03c_people.py`, input `normalization/json/personen_reise.json`, 64 people): diary days and kill sentences naming the person (surname; OCR variants like „Prönay“; surnames that are also nouns – Reiter, Koch, Sommer, Hermann – only after a title). GND: from the vault, else lobid-gnd, linked only if surname and first name match exactly (Karl = Carl), the record has life dates fitting 1892/93 and – for the crew – a naval or medical profession; otherwise `ambiguous`, `undated` or `implausible` with the candidates listed. Linked: Clam-Martinic, Becker (vault), Kinsky, Jedina, Lorenz-Liburnau, Ramberg, Plumert, Schleinitz (lobid). Not in the GND: Wurmbrand, Prónay, Havelock, Stockinger. Eduard Hodek's GND record is undated and its Wikidata item describes Hodek senior (b. 1827), not the son who travelled – left unlinked.
- Place coordinates come from Wikidata (P625); Nepal camps, Tjipandak, Badgery Station and Aru are approximate (`coord_note`).
