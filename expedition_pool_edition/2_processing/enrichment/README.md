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
python3 03d_objects.py        # Este collection objects (Weltmuseum) ↔ stops, diary, index cards → data/objects.json
python3 03e_europeana.py      # photos by the voyage's photographers in Europeana → data/europeana.json (needs EUROPEANA_API_KEY in .env)
python3 03f_person_sources.py # hunter, captain, photographers, doctors in all sources → data/person_sources.json
python3 04_build.py           # merge → data/enrichment.json, data/hunts.geojson
python3 05_export_presse.py   # ANNO clippings → ../../3_visualization/web/data/presse_anno.csv
python3 06_crosscheck_ffworld.py  # itinerary check vs franzferdinandsworld.com → data/ffworld_days.csv, ffworld_crosscheck.json
python3 07_heroes.py          # surviving animals (heroes.json, curated) → data/heroes.json, heroes.geojson
python3 08_export_prototype.py  # bundle for the prototype → ../../3_visualization/web/data/ke_enrichment.js
```

After step 5 rebuild the prototype bundle in `../kaiserin_elisabeth/`: `uv run python -m scripts.ke_diary`.
Step 8 then bundles the enrichment for `../../3_visualization/web/reise.html` (`data/ke_enrichment.js`,
`window.KEE`). The page is built on it: the 309 days of `normalization/json/tagebuch_tage.json` as the spine
(coordinates: hunting places from Wikidata first, then the prototype gazetteer, route places, a few stops by hand;
`coords` says which), the 18 episodes with their ANNO articles, the Europeana photos and the Este objects at the
day they are dated to, all 84 people of `data/people.json` (← `normalization/json/personen.json` + Ranglisten,
with diary days, GND/Wikidata, ANNO and Kulturpool hits), the person search and the live animals (`heroes.json`).
Views: days, hunts, animals, people, press echo (ANNO coverage, trophies/diary reviews, Kulturpool).
Deep links: `reise.html#1893-02-24`, `#hunt-1893-03-09-nepal`, `#fips-mucki`.
The bundle also feeds `geschichte.html` (the story page). Days after 24.8.1893 carry `"ship": false`: Franz
Ferdinand left S.M.S. Kaiserin Elisabeth in Yokohama and travelled home without her (`SHIP_END`, bundle key `ship`).
Every day with a map point carries `coord_source`: the method (`camp`, `hunt`, `hand`, `heading`, `site`,
`wikidata`), the basis (`wikidata`, `geonames`, `estimated`, `hand`), the Wikidata/GeoNames link and a note;
`reise.html` shows it in the day view. Hunting places that stand for several stops list them in
`places.json` as `camps` (the Nepal Terai camps, Alwar, Mullengudgery, Ugi, the Laroki camp, Shingle Creek):
with a Wikidata QID (coordinates fetched in step 0), a GeoNames point, or an estimate from the distances and
directions in the diary and Höfer's itinerary, each with a note.

ANNO evidence (step 2) is strict: a snippet counts only if it names Franz Ferdinand (not another archduke such as
his father Karl Ludwig, not "Erzherzogl." estates, regiments or hotels) and does not name only places or animals of
another hunt; an issue found for several hunts goes to the one whose place its snippet names (else the earliest).
Fewer hits (41 issues), but each one is about this hunt.

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
  europeana[]                    photos by the voyage's photographers dated on the episode's days: title, creators, provider, rights, europeana, preview, vf, animals
  objects[]                      Este objects acquired/described at this stop on the episode's days: inventory, type, url, strength, evidence, card
voyage
  kulturpool[]                   voyage-level objects (tier: voyage | modern)
  anno_coverage                  issues per month mentioning FF / FF + hunting, 12/1892–12/1893
  anno_topics[]                  "trophies" (1893–94), "diary" (reviews of the printed diary 1895–98)
```

Join to the normalised data via `places[].vault[].id` (= `_meta.id` in `normalization/json/ortschaften.json`),
`places[].wikidata`, or `diary.entries[].date` (= `date` in `normalization/json/tagebuch_tage.json`).
The whole route with coordinates is in `data/route_places.json` / `data/route.geojson`.

## Method and caveats

- **Hunts** come from keyword rules (aligned with `kaiserin_elisabeth/scripts/ke_diary.py`: bare "Strecke" usually means distance in the diary, so only "zur Strecke" counts) on the *uncorrected OCR* of the printed diary: a sentence with a killing verb (erlegen, schießen, zur Strecke, Beute …) and an animal from `animals.json`. `first_person` marks sentences with *ich/mir/mein* (FF himself rather than his companions). Counts are mentions, not the number of animals killed. Verbs and animal names must start at a word boundary ("verlegt" is no kill, "günstigerer" no tiger, "Momente" no duck); sentences about fish are skipped (cormorant fishing in Kyoto). Known noise: "Bär" in NSW is the koala ("Australischer Bär"); elephants are often ridden, not shot (partially filtered).
- **Episodes** are grouped by `places.json` → `region`; every episode at a known place with ≥2 kill sentences is enriched, bird hunts included (18 of 25; e.g. the flamingo hunt on Lake Manzala near Port Said, 20.12.1892, the first hunt of the voyage).
- **ANNO** (`https://anno.onb.ac.at/anno-suche/rest/search/…`, see the ÖNB Labs anno-notebook): window = first hunting day … last + 70 days. `near` = proximity query `"Erzherzog Tiger"~25` (precise); `issue` = `(Erzherzog OR Thronfolger) AND (place) AND (animal OR Jagd)` anywhere in the issue (broad). `relevance: high` = a snippet names the archduke together with the place or a specific animal (not just "Vögel", "Jagd", "erlegt"), or an issue-level hit whose snippet names the place (the archduke is often named a sentence earlier); `medium` = proximity hit only. Example: the Manzala hunt was widely reported (31.12.1892 – 6.1.1893), and the press speaks of crocodiles shot, which the diary does not mention. Snippet text is OCR and uncorrected.
- **Kulturpool** has little on the hunts themselves. `direct` objects (NHM Intendanzakten on the museum zoologist Ludwig Lorenz von Liburnau, who travelled with FF; the ÖNB guide to the voyage collections, 1894; the 2010 exhibition "Imperial Sightseeing") are found by seed searches + one hop of `/v2/similar?on=metadata`, then filtered by voyage-specific wording and year (1892–1899, or ≥1990 as `modern`). `context` objects only share a place name.
- **Höfer itinerary** (`../analyses/itinerary_1892_93.csv`, Höfer 2010): stays whose name matches the episode's diary spellings and that overlap the episode ±7 days. The Höfer span is often longer than the diary's hunting days (Nepal: 8–27 March vs. 10–26 March); all 20 regional episodes fall inside a Höfer stay.
- **Photos**: Weltmuseum Wien photos from `../analyses/vf_weltmuseum.csv` (VF numbers printed by Höfer, matched by the team; only `verified`/`variants_only` with a day date) and public-domain photos from the Wikimedia Commons API, linked by date to the episode's Höfer span. Weltmuseum pages state no licence, so only the link is kept. The 24 VF numbers marked `not_online` are not on the Weltmuseum site; Europeana has no Weltmuseum records and Kulturpool has none of these photos (checked 27.10.2026).
- **Vault ids** come from `normalization/json/ortschaften.json` (Lisa's filter of the vault); `places.json` stores the note titles. Three hunting places are not on the normalised route (Bharatpur; Banff and Penticton, travelled on another ship).
- **Heroes** (`heroes.json`, hand-curated): the live animals of the voyage – the ship's menagerie ("Bordmenagerie": monkeys Fips and Mucki, birds, a piglet, bears from Japan …) and animals sent to Vienna (Schönbrunn, the archduke's palace). Every claim cites a diary date or an ANNO issue and page; `06_heroes.py` checks each quote against its source and fails if one is not found. `status`: free / schoenbrunn / vienna / died / unknown; `evidence`: diary / press / probable (our inference, explained in `note`). ANNO's page full text sits behind a bot check, so press quotes are assembled from snippets; joins are marked with `…`.
- **Cross-check with franzferdinandsworld.com** (step 07, 27.10.2026): the site lists all 309 days (14.12.1892–18.10.1893) with a place, 284 with a page holding an English translation of that day. Against Höfer (304 days) and the diary headings (159 days) there is no contradiction: the differences are sea passages named differently, spellings/OCR, and stops on the way (Poona, Patna). Two problems on our side:
  - **The OCR diary has 170 entries, the book ~284 days.** The OCR lost many inline date headings, so 63 entries span several days. Fixed upstream: `../normalization/diary_days.py` splits the diary into days, and all steps now date by day. Leander's `../../3_visualization/web/data/ke_diary.json` is now built from the same days too (309 records; `ocr_entry` marks the 170 days with an OCR heading, which `06_crosscheck_ffworld.py` compares).
  - **Pages are missing from the OCR** (e.g. 31 March, 15 July: the drowned parrot, the steamer „Vindobona“ and the 14 monkeys). Those passages are cited from the site's translation (`site` quotes, checked against the cached page).
  - Höfer's table (`../analyses/itinerary_1892_93.csv`) has an empty stage for 1–4 January 1893.
- **People** (`03c_people.py`, input `normalization/json/personen_reise.json`, 84 people): diary days and kill sentences naming the person (surname; OCR variants like „Prönay“; surnames that are also nouns – Reiter, Koch, Sommer, Hermann – only after a title). GND: from the vault, else lobid-gnd, linked only if surname and first name match exactly (Karl = Carl), the record has life dates fitting 1892/93 and – for the crew – a naval or medical profession, for contacts (no crew evidence) a profession named in the vault note or matching life dates; otherwise `ambiguous`, `undated` or `implausible` with the candidates listed. Linked: Clam-Martinic, Becker (vault), Kinsky, Jedina, Lorenz-Liburnau, Ramberg, Plumert, Schleinitz (lobid); Lala Deen Dayal fixed by hand to GND 129514721 („Deen Dayal, Raja“, 1844–1905, Wikidata Q1182338, the record the Weltmuseum uses) – the GND also has 133576116 („Dayal, Lala Din“, †1910), probably a duplicate. The diary's animal keeper „Biaggio“ is searched as Blasius Paskoevič (probably the same person). Not in the GND: Wurmbrand, Prónay, Havelock, Stockinger. Eduard Hodek's GND record is undated and its Wikidata item describes Hodek senior (b. 1827), not the son who travelled – left unlinked.
- **Objects** (`03d_objects.py`, input `normalization/json/objekte.json`, 1,798 online objects of the Este collection): links to the voyage are suggestions with evidence. Place: the object's region (`Ortschaft (Route)`, else `Geografie`) → the diary days at that stop (`via` for regions FF did not visit but whose objects were sold at a stop: Tibet/Sikkim/Bhutan → Darjeeling, Moluccas → Amboina, Borneo → Kuching; „Indien“ alone gets no days). Diary: the object word (inflected, not inside a compound; materials and adjectives ignored) in a sentence on those days. `strong` (18) = that sentence speaks of buying or a gift, or the index card records a gift to the archduke – e.g. weapons bought in Hyderabad (25.1.), the gold inkstand the Nizam gave as a keepsake (26.1.), a powder horn in Jaipur, the Meiji emperor's carbine (card); `medium` (131) = the type is described in the diary at that stop, or the card names the School of Art / 1893; `place` = only the region fits. Animal motifs and materials are tagged, but a motif is no link to a hunt. Weltmuseum images are linked, not shown (no licence stated).
- **Europeana** (`03e_europeana.py`, key `EUROPEANA_API_KEY` from the environment or the repo's `.env`, never stored): images by the photographers who accompanied the voyage – Eduard Hodek jun. (on board), Lala Deen Dayal (Hyderabad), Max von Imhof (North America), prints by Carl Pietzner's studio; Bourne & Shepherd: none. Kept only if the creator field names the photographer (drops namesakes such as the Czech artist Josef Hodek) and the record belongs to the voyage (Weltmuseum VF photo, or Franz Ferdinand/voyage/ship named, or a stop together with a voyage date). Result 27.10.2026: 134 records – 131 Weltmuseum Wien (all also in `normalization/json/bilder.json`; licence **CC BY-NC-SA 4.0**, so they can be shown with attribution) and 3 Pietzner prints via The European Library (In Copyright statement, link only); 60 dated from the title, 37 on a hunting day. None of the 27 VF numbers marked not online in `Analysen/vf_weltmuseum.csv` is in Europeana. Europeana dates the Katni tiger photo 23.III.1893, the Weltmuseum list 22.III.1893.
- **Person search** (`03f_person_sources.py`): Janaczek (Leibjäger), Becker (captain), the photographers Ahrlé, Hodek, Ramberg, Reményi, Lala Deen Dayal, the doctors Bém and Plumert in the diary, the Weltmuseum exports, ANNO, Kulturpool, Europeana and Commons. Common names are searched with rank or ship next to them; a hit is kept only if it names the person together with their role or the voyage's context (Leibjäger, Linienschiffsarzt, Fähnrich, Elisabeth …; regiment names and adverts excluded) and falls in the voyage (15.12.1892–31.10.1893), its press echo (to 1894) or names the voyage/route. Raw and kept counts are stored per source. Finds: the photo of FF with his first tiger (Siriska, 24.2.1893, Weltmuseum VF_14454) carries the blind stamp „Fr. Ahrlé & Co. Photographers“; Ramberg took photographs on the voyage (diary 6.5.1893, Port Kennedy) and drew the equator diploma; Ramberg and Reményi were Linienschiffs-Fähnriche (press, Nov 1892 and the decorations of Dec 1893); Dr. Plumert published a hygienic topography of Pola (1892); Lala Deen Dayal: 32 photos of FF's visit to Hyderabad (Weltmuseum, via Europeana), none in the Austrian press. For Deen Dayal a stop of the route is not enough (he worked in Hyderabad for decades): a record must name the voyage/FF or be a Weltmuseum VF photo (FF's collection, `ff_collection`). Records of our time (the 2010 exhibition) are `modern`.
- Place coordinates come from Wikidata (P625); Nepal camps, Tjipandak, Badgery Station and Aru are approximate (`coord_note`).
