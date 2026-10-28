# JSON files – structure overview

Overview of every JSON file in `expedition_pool_edition/` (excluding `.venv` and the Obsidian config in `Vault/.obsidian/`).
Counts reflect the state of 2026-10-27.

**Notation:** `str`, `int`, `float`, `bool`, `null`, `[...]` = array, `{...}` = object.
`a | b` = the field takes either type. `?` = the field is not present in every record.

## Contents

1. [Data flow at a glance](#1-data-flow-at-a-glance)
2. [Shared conventions](#2-shared-conventions)
3. [`normalization/json/` – vault & museum data, normalized](#3-normalizationjson--vault--museum-data-normalized)
4. [`enrichment/` – hunts, animals, places, press, Kulturpool](#4-enrichment--hunts-animals-places-press-kulturpool)
5. [`3_visualization/web/data/` – map prototype data](#5-3_visualizationwebdata--map-prototype-data)
6. [`Analysen/` – summary statistics](#6-analysen--summary-statistics)
7. [`Sources/` – raw source metadata](#7-sources--raw-source-metadata)
8. [Shared IDs / how files link up](#8-shared-ids--how-files-link-up)

---

## 1. Data flow at a glance

```
Vault (Obsidian .md)  ─┐
Weltmuseum TMS export ─┼─► normalization/json/*.json ──► enrichment/data/*.json ──► prototypes / Analysen
Diary OCR (archive.org)┘        (German field names)        (English field names)
ANNO, Kulturpool, Wikidata, GND, Höfer 2010 ──────────────────────┘
```

| Folder | Field language | Purpose |
|---|---|---|
| `normalization/json/` | German (template field names from the vault) | One record per vault note / museum object |
| `enrichment/` | English | Links, coordinates, hunts, press coverage |
| `3_visualization/web/data/` | English | Ready-made data for the map/timeline prototype |
| `Analysen/`, `Sources/` | English | Statistics and source metadata |

---

## 2. Shared conventions

### Missing values (`normalization/json/`)
- Missing values are the **string `"NA"`**.
- Multi-value fields (e.g. `Geografie`, `Tierarten`, `Schiff`, `Auszeichnung`) are an **array when filled** (even with a single value) and the **string `"NA"` when empty**.
  → Always check `isinstance(value, list)` before iterating.
- In `enrichment/` and `kaiserin_elisabeth/`, missing values are `null` instead.

### The `_meta` block (every record in `normalization/json/`)

| Field | Type | Meaning |
|---|---|---|
| `id` | str | Stable ID, `ke-<typ>-<10 hex>` (e.g. `ke-person-17052a794e`) |
| `typ` | str | `person`, `place`, `ship`, `collection`, `object`, `image` |
| `datei` | str | Source vault note (e.g. `Personen/Ahrlé, Frederick.md`) or image file name; `"NA"` for objects |
| `created_by` | str | `human` (vault), `tms-export` (objects), `ai-assisted` (images) |
| `checked` | bool | Manually reviewed? (currently `false` almost everywhere) |
| `review` | `[str]` \| `"NA"` | Open issues, e.g. `"Link ohne Ziel: Afrika"`, `"Jahreszahl prüfen: 1992"` |
| `auswahlgrund` | [str] | Why the record was selected (e.g. `"Route der Weltreise (Kaiserin Elisabeth)"`) |
| `ki` | {…} ? | Images only: `{modell, datum, felder[]}` – which fields were AI-generated |

`bilder_tiere.json` only carries the reduced `_meta: {id, datei}`.

---

## 3. `normalization/json/` – vault & museum data, normalized

All files are a **top-level array of records**, except `weltreise*.json` and `tagebuch_tage.json` (single object).

> `*_final.json` variants: `ortschaften`, `schiffe`, `sammlungen_projekte` are byte-identical to their non-final version. `personen_final.json` (68) and `weltreise_final.json` differ – see below.

### `personen.json` · `personen_final.json` · `personen_reise.json` — people

| File | Records | Note |
|---|---|---|
| `personen.json` | 71 | All vault people linked to the voyage |
| `personen_final.json` | 68 | Cleaned subset |
| `personen_reise.json` | 82 | People actually on the voyage (crew from Ranglisten, entourage, hosts); adds `_reise` |

| Field | Type | Example |
|---|---|---|
| `Nachname, Vorname` | str | `"Clam-Martinic, Heinrich Graf"` |
| `Titel` | str | `"Graf"` |
| `Lebensdaten` | str | `"1842, Aue bei Schottwien - 1900, Fiume"` |
| `Beruf/Funktionen` | str | `"Fotograf"` (may contain Markdown links) |
| `Auszeichnung` | [str] \| "NA" | `["Seereise-Denkmünze 1892/1893"]` |
| `GND`, `VIAF`, `Lexikonbeitrag` | [str] \| "NA" | URLs |
| `Schiff` | [{`name`, `rollen`}] \| "NA" | `rollen`: [str] \| "NA" |
| `Ortschaft` | [str] \| "NA" | `["Triest (Domicil)"]` |
| `Länderbezug` | [str] \| "NA" | |
| `Archivalien mit Signatur`, `Goobi-Link zu den Archivalien`, `Literatur` | str | currently always "NA" |
| `Weitere Informationen mit Sammlungsbezug`, `Links zu Bezugspersonen`, `Quellen`, `Freitext` | [str] \| "NA" | |
| `Rolle auf der Weltreise` | [str] \| "NA" | `["Kapitän"]` |
| `_meta` | {…} | see §2 |
| `_reise` | {…} | **only `personen_reise.json`** |

`_reise` (only in `personen_reise.json`):

| Field | Type | Meaning |
|---|---|---|
| `gruppe` | str | `Besatzung` (71), `Gastgeber` (5), `Begleitung` (4), `Diener` (1), `Wissenschaft` (1) |
| `quelle` | str | Producing script (`filter_voyage.py`) |
| `rolle` | str ? | Free role, e.g. `"Kämmerer, Reisebegleiter"` |
| `ranglisten` | [{…}] ? | `{ranglisten_name, vorname_abweichend?, ranglisten: [{ausgabe, seite, dienstgrad, seit}]}` |
| `moegliche_dublette` | [str] ? | Possible duplicate person names |
| `vermutlich_dieselbe_wie` | str ? | Probably the same person as … |

### `ortschaften.json` (= `ortschaften_final.json`) — 49 route places

| Field | Type | Example |
|---|---|---|
| `Ort` | str | `"Pola, Istrien"` |
| `Region und Land` | [str] \| "NA" | `["Ägypten", "Levante"]` |
| `Geonames`, `GND Geographisches Schlagwort` | str | currently "NA" |
| `Schiff` | [str] \| "NA" | `["Kaiserin Elisabeth, Kreuzer"]` |
| `Personen (Link)` | [str] \| "NA" | |
| `Weitere Verknüpfungen` | [str] \| "NA" | |
| `Freitext` | [str] \| "NA" | |
| `Position auf der Route` | [int] | `[1]` – a place can appear several times |
| `_meta` | {…} | `typ: "place"` |

### `schiffe.json` (= `schiffe_final.json`) — 1 ship

| Field | Type |
|---|---|
| `Bezeichnung des Schiffes` | str (`"Kaiserin Elisabeth, Kreuzer"`) |
| `GND`, `Projekte`, `Archivbestände` | str ("NA") |
| `Reise` | {`Ziel der Reise`: str, `Jahr`: str, `Route`: [str], `Kapitän`: [str]} |
| `Objekte in der Sammlung` | [str] |
| `_meta` | {…} `typ: "ship"` |

### `sammlungen_projekte.json` (= `_final`) — 1 collection

`Institution oder Projekttitel` (str), `Website-Link zur Projektbeschreibung` ([str]), `Kontakt`, `Informationen zu den Beständen`, `Schiffe`, `Personen`, `Weitere Links`, `Freitext` (all str, currently "NA"), `_meta` (`typ: "collection"`).

### `weltreise.json` · `weltreise_final.json` — the voyage main entry (single object)

| Field | Type |
|---|---|
| `Titel` | str |
| `Beschreibung` | [str] (3 paragraphs) |
| `Schiff` | str |
| `Besatzung (laut Eintrag)` | [{`name`, `rolle`}] |
| `Route` | [str] (50 stops, in order) |
| `Route mit anderem Passagierschiff (nicht berücksichtigt)` | [str] (15 stops in Canada/USA) |
| `Anzahl Personen` | int (71 / **68** in `_final`) |
| `Anzahl Ortschaften` | int (49) |
| `Ortschaften ohne Eintrag` | str |
| `_meta` | {…} |

### `objekte.json` — 1,798 Weltmuseum objects (Sammlung Este)

| Field | Type | Example |
|---|---|---|
| `Inventarnummer` | str | `"VO_102004"` |
| `Objektbezeichnung`, `Titel` | str | `"Satteltasche"`, `"SATTELTASCHE"` |
| `Datierung`, `Material`, `Maße`, `Beschreibung`, `Abteilung` | str | |
| `Inventarband` | [str] | `["VIO_Este_1", …]` |
| `Este-Nummer` | str | |
| `Geografie`, `Geografie-Pfad` | [str] | `["Südasien > Subkontinent > Indien"]` |
| `Ortschaft (Route)` | [str] \| "NA" | matching route place, if any |
| `Karteikarte` | [str] \| "NA" | `["VO_KK_102004"]` |
| `Weltmuseum-Link` | str | object page URL |
| `Bild-Link` | [str] | image URLs |
| `Transkription` | [{`karteikarte`, `bild-link`, `text`}] \| "NA" | OCR of the index card |
| `_meta` | {…} | `typ: "object"`, `created_by: "tms-export"` |

### `bilder.json` — 408 voyage photographs (Weltmuseum, VF_…)

| Field | Type | Example / meaning |
|---|---|---|
| `Datei` | str | `"VF_14356.jpg"` |
| `Inventarnummer` | [str] | `["VF_14356"]` |
| `Titel`, `Datierung` | str | |
| `Geografie`, `Geografie-Pfad` | [str] \| "NA" | |
| `Ortschaft (Route)` | [str] \| "NA" | |
| `Weltmuseum-Link`, `Bild-Link` | [str] | |
| `Bildbeschreibung` | str | AI-generated description |
| `Tiere` | bool | animal visible? (AI) |
| `Tierarten` | [str] \| "NA" | AI-detected animals (German) |
| `_meta` | {…} | incl. `ki: {modell, datum, felder}` |

### `bilder_tiere.json` — 178 photographs with animals (output of `animal_pictures.py`)

| Field | Type | Meaning |
|---|---|---|
| `Titel`, `Datierung` | str | |
| `Inventarnummer`, `Bild-Link`, `Weltmuseum-Link` | [str] | |
| `Geografie`, `Geografie-Pfad` | [str] \| "NA" | |
| `Tierarten` | [str] | from `bilder.json` |
| `depicted_animals` | [str] \| "NA" | animals confirmed in the picture (98 filled) |
| `photographer` | str | `"Eduard Hodek jun."` (62) or `"NA"` (116) |
| `Tierarten (Bild-KI)` | [{`Tier`: str, `Score`: float}] \| "NA" | image-classifier result |
| `_meta` | {`id`, `datei`} | reduced |

### `tagebuch_tage.json` — Franz Ferdinand's diary, one entry per day (single object)

```
{ about: str, source_days: str (URL), days: [309 × day] }
```

| `days[]` field | Type | Meaning |
|---|---|---|
| `date` | str | ISO date |
| `place_site` | str | place according to franzferdinandsworld.com |
| `heading_ocr` | str \| null | diary chapter heading (OCR) |
| `entry_date` | str \| null | date of the diary entry covering this day |
| `band` | int \| null | volume 1 or 2 |
| `scan` | int \| null | scan/page number on archive.org |
| `page_url`, `site_url` | str \| null | |
| `method` | str | `aligned` (176), `heading` (107), `no_entry` (26) |
| `days_in_entry` | int | number of days covered by the entry |
| `text` | str | OCR text (uncorrected) |

---

## 4. `enrichment/` – hunts, animals, places, press, Kulturpool

### Lookup tables (`enrichment/*.json`)

| File | Top level | Record fields |
|---|---|---|
| `animals.json` | [17] | `id` (`"tiger"`), `de`, `en`, `pattern` (regex for the diary), `anno` ([str] newspaper search terms) |
| `places.json` | [28] | `id`, `region`, `label`, `diary` [str], `anno` [str], `wikidata` str\|null, `lat`, `lon`, `vault` [str], `coord_note?` |
| `route_wikidata.json` | {place name → {…}} (51) | `wikidata` str\|null, `coord_note?`, `lat?`, `lon?` (manual overrides) |
| `heroes.json` | {…} | hand-curated input for `data/heroes.json` (same structure, without resolved coordinates/URLs, plus a `places` lookup `{id: {label, wikidata, lat, lon, coord_note?}}`) |

### `data/places_resolved.json` — [28]
Like `places.json`, but `vault` is `[{note, id}]` (vault IDs resolved) plus `coords_from` (`"wikidata"`) and `on_route` (bool).

### `data/route_places.json` — 49 route places with coordinates
```
{ source: str, places: [{vault_id, vault_note, label, route_positions: [int],
                         wikidata, wikidata_label, lat, lon, coords_from, coord_note}] }
```

### `data/hunt_entries.json` — [73] diary entries describing a hunt

| Field | Type | Meaning |
|---|---|---|
| `date`, `place_raw` | str | |
| `place_id`, `region` | str \| null | → `places.json` `id` |
| `band`, `scan`, `page_url` | int / str | diary location |
| `day_method` | str | `aligned` / `heading` |
| `animals` | {animal id → int} | mentions per animal (e.g. `{"tiger": 2}`) |
| `kill_sentences`, `first_person` | int | |
| `quotes` | [{`text`, `animals`: [str], `first_person`: bool}] | |
| `kills` | [str] | kill sentences |

### `data/hunts.json` — [31] hunt episodes (entries grouped)
`id` (`"hunt-1892-12-20-port-said"`), `region`, `place_ids` [str], `place_raw`, `start`, `end`, `animals` {id → int}, `kill_sentences`, `diary` [{date, band, scan}], `quotes` [{text, animals, first_person, date, band, scan}].

### `data/anno.json` — newspaper hits (ANNO, Austrian National Library)

```
{ source, api,
  episodes: [12 × {hunt_id, window: [from, to], queries: {near: {text}, issue: {text}},
                   documents: [{docId, title, date, newspaper, pub_place, url, thumbnail,
                                hits_in_issue, match: [str], snippets?: [{page, text}], relevance?}]}],
  coverage: {query_hunting, query_all, months: [{month, issues_ff_hunting, issues_ff}]},
  topics: [{id, label, query, start, end, total, documents: [...]}] }
```

### `data/kulturpool.json` — Kulturpool records

```
{ source,
  direct:   [11 × KulturpoolItem],
  episodes: [12 × {hunt_id, direct: [item id], context: [KulturpoolItem]}] }
```
**KulturpoolItem:** `id`, `title`, `provider`, `description`, `date` [str]\|null, `spatial` [str]\|null, `type` [str], `url`, `isShownAt`, `image`, `iiif` str\|null, `rights`, `found_by`, `year` int\|null, `tier`.

### `data/hoefer_photos.json` — photos according to Höfer (2010)
```
{ sources: {hoefer, weltmuseum, commons},
  episodes: [22 × {hunt_id,
                   hoefer: {stays: [{stay, from, to, section}], from, to,
                            days_without_hunting_entry, diary_within_hoefer},
                   photos: [Photo]}] }
```
**Photo:** `source`, `vf_id?`, `title`, `date`, `date_to?`, `status?` (`verified` / `variants_only`), `geography?`, `url`, `rights`, `image`, `note?`, `description?`, `creator?`, `credit?`.

### `data/objects.json` — all 1,798 objects, each rated for its link to the voyage
```
{ source, about, summary: {strong: 18, medium: 131, place: 671, none: 978}, objects: [1798 × Object] }
```

| Object field | Type | Meaning |
|---|---|---|
| `id` | str | = `_meta.id` in `objekte.json` |
| `inventory`, `type`, `title`, `dating`, `material`, `url`, `image` | str | |
| `geography` | [str] | |
| `stay` | [{`region`, `kind` (`direct`/`via`), `from` (`Geografie`/`Ortschaft (Route)`), `first`, `last`, `days`, `dates`: [str]}] | when the voyage was in that region |
| `diary` | [{`date`, `place`, `scan`, `page_url`, `match`: [str], `acquisition`: bool, `text`}] | matching diary sentences |
| `card` | [{`kind`, `text`}] | index-card evidence; `kind`: `collected_1893`, `school_of_art`, `gift_to_ff`, `occasion` |
| `animals`, `animal_material`, `hunts_here` | [str] | |
| `strength` | str | link strength: `strong` / `medium` / `place` / `none` |

### `data/people.json` — the 82 voyage people, enriched
```
{ source: "normalization/json/personen_reise.json", people: [82 × Person] }
```

| Person field | Type | Meaning |
|---|---|---|
| `id` | str | = `_meta.id` in `personen_reise.json` |
| `name`, `group` | str | `group` = `_reise.gruppe` |
| `role` | str \| null | |
| `ranks` | [str] | ranks from the Ranglisten |
| `vault_note`, `life_vault` | str \| null | |
| `possible_duplicate` | [str] \| null | |
| `diary` | {`pattern`, `days`, `first`, `last`, `dates`: [str], `kill_sentences`, `hunts`: [str], `kills_by_hunt`: {hunt id → int}, `kill_quotes`: [{date, text}]} | name mentions in the diary |
| `gnd` | {`status`, `id`, `candidates`, `name`, `born`, `died`, `professions`: [str], `url`, `wikidata`} | `status`: `none`, `not_searched`, `undated`, `lobid`, `implausible`, `vault` |
| `wikidata`, `wikidata_label?`, `wikidata_description?` | str \| null | |
| `anno` | {`query`, `total`, `examples`: [...]} \| null | |
| `kulturpool` | {`found`, `items`: [...]} \| null | |

### `data/heroes.json` — the voyage's live animals ("Bordmenagerie")
```
{ about, people: [2 × Keeper], heroes: [17 × Hero], summary_press: [Press] }
```
- **Hero:** `id`, `name`, `species_de`, `species_en`, `count` int\|null, `status` (`schoenbrunn` / `died` / `unknown` / `free` / `vienna`), `evidence` (`diary` / `press` / `probable` / `site`), `route` [{place, date, event, label, lat, lon, wikidata, coord_note, evidence?}], `diary` [{date, quote, band, scan, page_url}], `press` [Press], `site` [{day, quote, url, source}], `note?`, `latin_in_source?`, `intended?` {place, label, evidence, lat, lon, wikidata}
- **Keeper:** `id`, `name`, `role`, `diary`, `press`, `site` (as above)
- **Press:** `doc` (ANNO docId), `page`, `quote`, `newspaper`, `date`, `url`

### `data/ffworld_crosscheck.json` — franzferdinandsworld.com vs. diary/Höfer
```
{ source, checked: date,
  summary: {site_days, site_pages, diary_entries, hoefer_days_compared,
            hoefer_disagreements: {sea_or_leg, spelling}, diary_days_compared,
            diary_disagreements: {sea_or_leg, review, spelling},
            diary_entries_spanning_several_site_days, site_days_inside_such_entries},
  disagreements: {hoefer: [{date, site, hoefer, kind}], diary: [{date, site, diary, kind}]},
  multi_day_entries: [{entry, heading, site_days: [str]}] }
```

### `data/enrichment.json` — **everything combined per hunt episode** (main product)
```
{ meta: {title, sources: {diary, anno, kulturpool}, method},
  episodes: [12 × Episode],
  voyage: {objects_strong: [Object], kulturpool: [KulturpoolItem],
           anno_coverage: {...}, anno_topics: [...]} }
```

| Episode field | Content |
|---|---|
| `id`, `region`, `start`, `end` | hunt episode (= `hunts.json` id) |
| `places` | [{id, label, lat, lon, wikidata, coord_note, vault: [{note, id}], on_route}] |
| `animals` | [{id, label_de, label_en, mentions}] |
| `diary` | {entries: [{date, band, scan}], kill_sentences, quotes: [...]} |
| `anno` | {window, queries, issues_found, issues_high, articles: [ANNO document]} |
| `kulturpool` | {direct: [KulturpoolItem], context: [KulturpoolItem]} |
| `hoefer` | {stays, from, to, days_without_hunting_entry, diary_within_hoefer} |
| `photos` | [Photo] (see `hoefer_photos.json`) |
| `objects` | [{id, inventory, type, title, url, strength, evidence: {date, place, scan, page_url, match, acquisition, text} \| null, card}] |
| `people` | [{id, name, group, kill_sentences, gnd, wikidata}] |

---

## 5. `3_visualization/web/data/` – map prototype data

### `data/ke_diary.json` — [309] diary days with location

One record per day (from `2_processing/normalization/json/tagebuch_tage.json`). `date`, `band`, `scan`, `page_url`, `heading` (OCR heading, only on days that have one), `kind` (`stay` / `at_sea` / `transfer` / `unknown`), `place_as_printed`, `place_source` (`heading` / `site` / empty), `place`, `country` (ISO code), `lat`/`lon` (float\|null; only for heading places), `geonames` (URL), `place_site` (franzferdinandsworld.com), `ocr_entry` (bool: the OCR has a heading on this day, 170 days), `entry_date`, `method` (of the day split), `words` (int), `kill_sentences` (int), `animals_in_kill_sentences` [str], `kill_quotes` [str].

### `data/ke_layers.json` — per-day layers for the timeline
```
{ days: {"1892-12-15": Day, ... (170 days)},
  voyage: {medal_holders: [str], kulturpool_context: [{section, label, text, url}],
           hoefer_photos: [{vf_id, page, stops}]},
  rules: {aboard: str, actors: str, collecting: str} }   ← text explaining how each layer is computed
```
**Day:** `heading`, `location`, `place_note`, `aboard_issue` (Rangliste issue date), `aboard` [{name, rank, seit, medal_note}], `aboard_by_rank` {rank → count}, `actors` [{note, folder}], `collecting` [str].

> ⚠️ `voyage.medal_holders` contains the template note name `"0_Muster_Personen"` – probably a leaked vault template.

### `data/ke_places.lpf.json` — GeoJSON / Linked Places Format (59 features)
```
{ type: "FeatureCollection", @context, features: [{
    @id: "ke:place/pola-istrien", type: "Feature",
    properties: {title, ccodes: [str], segments: [str]},
    geometry: {type: "Point", coordinates: [lon, lat]},
    names: [{toponym, lang, citations: [{label, ...}], when?}],
    links: [{type: "closeMatch", identifier: URL}],
    when: {timespans: [{start: {in}, end: {in}}]} }] }
```

### `data/ke_stop_records.json` — [70] route stops with Kulturpool hits
`segment`, `label`, `years`, `on_ship`, `seq`, `place_note`, `geo_status`, `geo_matched`, `geo_name`, `historic_names`, `country`, `geonames`, `ambiguous`, `latitude`, `longitude`, `window` — **all strings** (CSV origin, incl. `"True"`/`"44.86"`), plus `query_names` [str], `kp_found` int, `kp_records` [{id, title, provider, date, licence, open: bool, image, url}].

### `arcgis/ke_photos_summary.json` — photo-mapping statistics (single object)
Counts (`photos_in_team_file`, `day_dated_mapped_rows`, `no_day_date`, `outside_route`, `with_coordinates`, `without_coordinates`), `coord_source` {stop, geonames, geonames_rejected, none}, `day_kind` {stay, travel, none}, `g2_route_vs_museum` {…counts}, `g2_pairs_to_read` [str], `control_verified_photos` [{vf_id, place_of_day, museum_geography, string_fit}], `places_without_coordinates` [str].

---

## 6. `Analysen/` – summary statistics

| File | Structure |
|---|---|
| `compare_summary.json` | Diary vs. Höfer itinerary: `diary_days`, `diary_span` [from, to], `hoefer_rows`, `hoefer_span`, `calendar_days_in_span`, `hoefer_days_covered`, `diary_days_without_hoefer_row`, `hoefer_days_without_diary_entry`, `place_check` {agree, disagree, no_hoefer_place, no_diary_place}, `kind_check` {agree, disagree, diary_unknown} |
| `itinerary_summary.json` | Höfer itinerary: `rows`, `dated_rows`, `date_range`, `total_row`, `sections` [str], `stops_considered`, `stops_with_dates`, `stays_not_in_prototype`, `stays_not_in_prototype_list` [str] |
| `anno_presse/summary.json` | Press coverage of the ship: `source`, `months`, `lag_days`, `max_docs_per_month`, `terms` [str], `docs`, `rows`, `rows_without_leg`, `per_query_month` [{query, month, total_hits, fetched, new_docs, capped}] |

---

## 7. `Sources/` – raw source metadata

`tagebuchmeinerr00ferdgoog_page_numbers.json` (584 pages) and `tagebuchmeinerr01ferdgoog_page_numbers.json` (554 pages) — archive.org page-number detection for the two diary volumes:
```
{ identifier, format-version, archive-hocr-tools-version, confidence: int,
  pages: [{leafNum: int, pageNumber: str, confidence, pageProb, wordConf: int|null}] }
```
`leafNum` = scan index (`scan` / `/page/n…` in diary URLs), `pageNumber` = printed page number.

---

## 8. Shared IDs / how files link up

| Key | Format | Appears in |
|---|---|---|
| Vault ID | `ke-person-…`, `ke-place-…`, `ke-object-…`, `ke-image-…`, `ke-ship-…`, `ke-collection-…` | `_meta.id` (normalization) → `id` / `vault_id` / `vault[].id` (enrichment) |
| Hunt ID | `hunt-YYYY-MM-DD-<region>` | `hunts.json`, `enrichment.json`, `anno.json`, `kulturpool.json`, `hoefer_photos.json`, `objects[].hunts_here`, `people[].diary.hunts` |
| Place ID | slug, e.g. `port-said` | `places.json`, `places_resolved.json`, `hunt_entries.place_id`, `hunts.place_ids` |
| Animal ID | English slug, e.g. `tiger` | `animals.json`, `animals` objects/arrays in hunts, objects, episodes |
| Inventory no. | `VO_…` (objects), `VF_…` (photos), `VO_KK_…` (index cards) | `objekte.json`, `bilder*.json`, `objects.json`, `vf_id` in photo lists |
| ANNO docId | `ANNO_<paper><yyyymmdd>` | `anno.json`, `press[].doc` in heroes |
| Diary page | `band` + `scan` → `page_url` | diary, hunts, objects, heroes, `ke_diary.json` |
| Date | ISO `YYYY-MM-DD` | everywhere outside `normalization/` (there: free-text `Datierung`) |
