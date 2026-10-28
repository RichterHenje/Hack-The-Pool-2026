# ArcGIS Online: scripted demo layers (27.10.2026)

Org `cacgeoportal-hub.maps.arcgis.com`, the owner's account (role publisher, user type
HUBMemberUT, **cannot create groups**; the org is a foreign Hub community, so "Organisation"
is not JKU). Everything below is **private**. There is no team-only share: either the owner
presents it, or it goes public (= publishing, waits for the licence decision).

## How it runs

No Python login. The owner signs in in Chrome; Claude runs the script in a tab on any
`/sharing/rest?f=json` page of the org (claude-in-chrome `javascript_tool`). The token comes
from `oauth2/platformSelf` inside the page and is never returned. Open a fresh page per run
(top-level `const`s collide otherwise).

- `ke_publish.js`: `RUN = 'test'` (3-row date test, then `delete:<id>`), `'publish'` (all
  four layers). createService → addToDefinition (admin URL) → addFeatures from the team's
  GeoJSON at a pinned commit; dates as epoch ms at 12:00 UTC.
  - The full publish ran longer than the tool's 45 s limit; the page kept running and
    finished. Check with a search before re-running, or publish one layer per call.
- `ke_webmap.js`: starter web map over the four layers.

## Results (27.10., data khm-team `b5e1464`)

Date test passed: `esriFieldTypeDate`, 1892-12-15 read back as -2431252800000 ms
(exact), null stays null, `arrival_date >= DATE '1893-01-01'` returns only the 1893 row,
access private. Test item deleted.

| item | id | features | time |
| --- | --- | ---: | --- |
| KE 1892-93 Stationen (`KE1893_stops`) | 6a005afe2e294c78bf1f1d0dc807ad56 | 48 (1 without date: Pola) | arrival_date, 1892-12-15..1893-10-17 |
| KE 1892-93 Etappen (`KE1893_legs`) | a79a79039fe545559c5fe540a72d4575 | 47 (1 without date: Pola→Triest) | date_from–date_to |
| KE 1892-93 Fotos Weltmuseum (Links) (`KE1893_photos`) | fc459046ad9e4bc5b2372e9676870fe2 | 87 (the GeoJSON keeps only rows with coordinates; 159 in the CSV) | photo_date (renamed from `date`), 1893-01-17..1893-10-08 |
| KE 1892-93 Jagden (`KE1893_hunts`) | 53d27a6c989d423ab71bb0b13e5f42ee | 12 | date_from–date_to |
| Web map "SMS Kaiserin Elisabeth 1892–93 (Demo)" | 977298da4e1a47c380c77a9041e11908 | 4 layers, 6 bookmarks | slider 1 day, current interval |

Map Viewer: https://cacgeoportal-hub.maps.arcgis.com/apps/mapviewer/index.html?webmap=977298da4e1a47c380c77a9041e11908

### v2 (27.10. ~00:30, `ke_webmap_v2.js`, written in place over the same item; v1 script = backup)

Checked in Map Viewer by screenshot: opens; basemap Vintage Shaded Relief (j_nelson, no
labels, credits shown); labels "Bombay (Mumbai)", "Batavia (Jakarta)", "Kanton (Guangzhou)";
stops filled (Kulturpool names the place 1892–93) vs hollow (does not); bookmarks carry time
extents and set the slider (bookmark 3: 15.12.1892–9.3.1893, all inland Indian stops hollow,
Calcutta filled); Delhi pop-up wording as intended. **Not honoured:** progressive slider
(`thumbMoves: false`): both thumbs move during play; switch in the slider gear menu by hand.
Not checked: photo pop-up, bookmark 5 at the date line, hunts pop-up. Small: "Pilibhit
(Pilibhit)" label (name_now differs only invisibly). 1914 boundaries layer rejected (Triest
in "Italy", see docs/14). After this, the map belongs to the owner: no more script updates.

### v3–v6 and extra layer (28.10. ~01:00–02:30), all patches read the saved JSON and change parts

Order matters; a rerun from scratch must repeat the manual step.
1. **Manual, in Map Viewer:** time slider options → "Show data progressively" → Save. Stored as
   `widgets.timeSlider.properties.thumbCount: 1` (my `thumbMoves: false` in v2 was ignored);
   playback speed is `thumbMovingRate` (ms per step).
2. `ke_photos_images.js`: field `image_url` on KE1893_photos, 87/87 filled from the team's
   `bilder.json` (owner decision: Weltmuseum images may be shown in the private demo).
3. `ke_webmap_v3_patch.js`: playback 300 ms/day, start on day 1, German dates, labels ignore
   diacritic-only differences, photo pop-up with image, cluster labels + cluster pop-up.
4. `ke_webmap_v4_legs.js`: legs legend and pop-up (on_ship is a route section, not "on board").
5. `ke_publish.js` with `RUN = 'publish:press'`: **KE1893_press**, item
   46dbaff0a0ea4deab74859ae26880b1e, 69 features, time field `date_published`.
6. `ke_webmap_v5_press.js`: press layer in the map, hunts sized by `kill_sentences` (4–39).
7. `ke_webmap_v6_qm.js`: QM wording fixes (docs/15_map_qm.md).
8. `ke_webmap_v7_photofilter.js`: map-level filter hides 21 photos whose museum geography
   contradicts the route place (66 of 87 shown; hosted layer unchanged).
9. **Presentation:** Exhibit without a saved app item, slides = the 6 bookmarks (time included),
    click-through (no auto-play):
    https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?webmap=977298da4e1a47c380c77a9041e11908
    Fallback for the slam (not in git, in the owner's Downloads): `ke1893_exhibit_tour.gif`
    (6 slides) and `ke1893_slides/*.png` (stills).
### v8–v9: team data integrated (28.10. ~03:15–04:45), source `ke_enrichment.js` at khm-team b5e1464

All transforms run in the page and fetch the team file from raw.githubusercontent at the pinned SHA.
- `ke_photos_rights.js`: licence, photographer, Europeana link for 58 of our 87 photos (team list:
  134 Europeana records, 131 CC BY-NC-SA 4.0, 3 InC); caption "…, Weltmuseum Wien, CC BY-NC-SA 4.0
  (über Europeana; Aggregator: Kulturpool)", else "Lizenz nicht geprüft".
- `ke_layer_days.js`: **KE1893_days**, item 0bfc650e853949dc8c82618f50c0e18f, 206 of 309 diary days
  (those with coordinates); pop-up with archive.org scan, English day page, day method, coordinate source.
- `ke_refill_hunts_press.js`: KE1893_hunts 12 → **18** episodes (our 12 came from an export made before
  the team added the bird hunts, commit 1f2b7cc); KE1893_press 69 → **104** (enrichment pipeline,
  relevance high 64 / medium 40). Refilled in place (delete + add), so URLs and filters stay valid.
- `ke_layer_objects.js`: **KE1893_objects**, item 32d663a04d8f4e82b2913c368fef4ad7, 136 of 149 Este
  objects placed via their diary day; strong 18 / medium 131.
- `ke_webmap_v9_fixes.js`: day title; map shows only the 18 strong object links.
- Lesson: `<` or `>` in OCR text makes ArcGIS reject the record ("Field … has unsafe html content",
  xssPrevention); `clean()` now maps them to ‹ ›.

### v10: all photos, kill layer, QM (28.10. ~05:15–06:30)

- `ke_layer_photos_all.js`: **KE1893_photos_all**, item 83168e4e37ed442698036078788680d2: all 408
  Weltmuseum photos of the team list (`bilder.json`), **357 placed**, 51 not (they name only a region).
  ONE rule: the point is the place the museum/team names, not Franz Ferdinand's position.
  Tiers: A 236 'Ortschaft (Route)' → team gazetteer; A2 6 'Geografie' → same; B 96 'Geografie' →
  Wikidata (`photo_places_wikidata.json`, 25 places, country-checked, resolved in the browser because
  the API rate-limited the script); T 19 'Terai' → team's Nepal hunt place (approximate).
  Day dates from the team's `ke_photos_dated.csv`: 128 placed photos dated. In the map as two layers
  on one service: "mit Tagesdatum" (time slider) and "ohne Tagesdatum" (`timeAnimation: false`,
  off by default). The old KE1893_photos (route-based placement) is removed from the map (item
  kept), which also retires the v7 filter.
- `ke_layer_kills.js`: **KE1893_kills**, item 5cccd75ead8f4e42901c3e0439393928: 65 day entries from
  `hunt_entries.json`; 57 with first-person sentences; 4 without place_id (Benares, Singapore,
  Sydney, Nouméa, one sentence each, no hunt episode) placed at the diary day and marked.
- `ke_qm_check.js`: read-only QM over all layers (counts, private, read-only, time extent, field and
  expression references, definition expressions, sample images, link formats). Round 1 found 4
  diary days without scan link and empty "Jagd:" text (fixed in `ke_webmap_v10_qm.js`); round 2: none.
- The GIF/PNG fallbacks in Downloads predate v8–v10 (they show the six bookmarks, not the new layers).

10. Not scripted (one REST call, 28.10. ~02:20): `initialState.viewpoint` reset to the whole
   route (-130,-45 to 179,62, Web Mercator); a Map Viewer save had stored the India view.

v1 notes: Not checked by Claude (Map Viewer pages do not load for the extension): how the map renders,
the time slider, clustering, labels. Basemap is the org default ("Vintage Shaded Relief" not
found by search): switch by hand. Earlier hand uploads (`ke_*` GeoJSON items, 27.10.
16:03–16:13) are the owner's and were not touched.

### Fix 28.10. ~10:40: Kulturpool search links

The portal's search parameter is `query`, not `q` (`https://kulturpool.at/suche?query="Singapur"`;
reported by the owner). Source: `scripts/ke_arcgis_pack.py` (fixed, `prototype/arcgis/ke_stops.*`
regenerated, only the URLs changed). Hosted layer KE1893_stops: field `kp_search_url` rewritten in
place with `updateFeatures` (48/48, read back uncached: 0 `?q=`, 48 `?query=`; the service caches
queries for 30 s). The team's copies (`kaiserin_elisabeth/scripts/ke_arcgis_pack.py`,
`prototype/arcgis/ke_stops*.{csv,geojson}`, `ke_stops_dated.*`) still carry `?q=`: the team fixes
them, nothing was written to the team repo.

### Provenance texts (28.10. ~10:35)

One source of truth, `scripts/arcgis/ke_sources.json` (bibliography + per-layer origin, checks,
status, rights), rendered by `uv run python -m scripts.arcgis_provenance` with counts from the live
layers (`ke_provenance_counts.js` → `provenance_counts_2026-10-28.json`, read-only) into
`ke_metadata_payload.json` and `docs/21_data_provenance.md`. `ke_metadata.js` wrote snippet,
description, credits (accessInformation) and licenceInfo of the 8 layer items and the web map
(legs first as a test, then 4 + 3 + map); every field read back equal as text, all still private,
web map data byte-identical. Exhibit's Details panel and attribution read these fields. Also
corrected: the old map text said photos sit where Franz Ferdinand was (rule retired in v10).
Status words: "checked by a person" (none yet on any layer), "machine-made, unchecked",
"rule-based". Open: the team's data licence (written as "to be confirmed by the team").

### Pop-up source footers (28.10. ~10:50)

`ke_popup_footers.js` (MODE 'add'; 'remove' takes them out) appended one German text element
"Quelle · Status · Rechte · Mehr: Beschreibung der Ebene" to all 9 pop-ups; wording in
`ke_sources.json` (`footer_de`), rendered with the payload. Read back: 9/9 footers, rest of the web
map identical, 9 layers, 6 bookmarks. `ke_qm_check.js` afterwards: no issues, 12/12 images load.
A Map Viewer tab left open with older unsaved state would overwrite the footers on save.

### Team data update a4b8b5a (28.10. ~11:30)

Team branch moved b5e1464 → a4b8b5a (4 commits 09:20–10:32). Semantic diff of `ke_enrichment.js`:
days 206 → 216 with a point (10 new, 31 moved, two Livingston days by ~2,960 km), new `coord_source`
(method, basis, ref, note); Nepal episode only its coord_note; `places.json` +camps (6 places, place
points unchanged); `route_places` Dakna Bâgh, Beli moved to camps; GeoNames lost 'Livingston'.
Press, objects, photo list, stations, legs unchanged. Checked per layer which features depend on the
moved inputs: kills (the 4 day-fallback dates did not move), hunts/press (episode place 0 unchanged),
photos (no Ortschaft Dakna/Beli; 2 photos with geography 'Livingston' sat in New Jersey).
`ke_refill_days.js`: days refilled in place (216, labels as in the team's reise.js, new fields
coord_basis(_de), coord_name, coord_ref, coord_note; pop-up line "Koordinate: … · Basis Beleg — note";
guard: stops before any write if the pop-up line is not found), 2 Livingston photos → Montana
(45.6619, −110.5605), Nepal hunt note. Checks: Kala Wewa days 5.–12.1. unchanged (slide 2),
time extent unchanged, capabilities Query. Provenance re-rendered from `provenance_counts_2026-10-28b.json`
(per-layer data commit), all 9 items rewritten and read back, days footer replaced; `ke_qm_check.js`
(EXPECT days 216, new coord_ref format check): no issues.

### Export (28.10. ~12:05)

`ke_export.js` (read-only) saved one bundle from the browser (`ke_arcgis_export_2026-10-28.json`, owner's
Downloads, 792 KB, no token); `uv run python -m scripts.arcgis_export_split <bundle>` split it into
`prototype/arcgis/export_2026-10-28/`: one GeoJSON per hosted service (legs 47, days 216, stops 48,
hunts 18, kills 65, objects 136, press 104, photos 357; the two photo map layers are filters on one
service, see `layers.json`), `webmap.json`, `items.json`, `layers.json`, `MANIFEST.md` (counts, SHA-256).

### Apps, review loop, public (28.10. ~12:15–13:05)

- Apps created by clicking in the Instant Apps gallery (it renders for the extension; Map Viewer
  does not): Exhibit `c79ee6edf2084f31b3a2f7e0be943596`, Slider `63327c035045432f95793e26965e0d39`,
  default settings, both on this web map. Seen in the app: Exhibit slides set the view only; the
  bookmarks' time extents are not applied.
- Review fixes, each read back: services' `copyrightText` was empty (set to the item credits, service
  and layer 0, all 8); stations Livingston (GeoNames 5100572, New Jersey) → Livingston, Montana
  (-110.5605, 45.6619) and Wyoming (5015618, Michigan) → Yellowstone NP (Wikidata Q351, -110.5, 44.6),
  legs Spokane–Livingston–Wyoming–Chicago redrawn as great circles; Tjiandjur arrival 6.5. (estimated
  although `hoefer_from` = 15.4.) → 15.4.1893, legs Buitenzorg–Tjiandjur 12.4.–15.4. (first Buitenzorg
  visit) and its `estimated` flag 0; 3 kill entries at 0/0 → diary day's point (cause: `lat: 0, lon: 0`
  placeholders for gwalior/owaraha in the team's `enrichment/places.json`; `ke_layer_kills.js` now
  treats 0/0 as missing).
- Checked and left: 59 points > 500 km from the nearest station are real places off the station list
  (Aden, Thursday Island, Solomon Islands, Kuching, Yellowstone, Colorado, Salt Lake City). Colombo has
  no placed diary day within ±3 days of its arrival.
- `ke_qm_check.js`: expects `public`; new checks for points at 0/0, legs ending before they start, and
  stations > 300 km from the diary days within ±3 days of their arrival. Run after the fixes: no issues.
- Shared to Everyone (owner decision): web map, 8 layers, 2 apps; checked logged out. Texts: "private
  demo" wording removed, correction notes added to stations, legs, kill entries; counts snapshot
  `provenance_counts_2026-10-28c.json` (estimated stations 5, legs 10; hash equal to the live run);
  all 36 item text fields equal to the rendering (SHA-256 of the plain text, read logged out).
- Re-export into `prototype/arcgis/export_2026-10-28/` (overwritten; bundle
  `ke_arcgis_export_2026-10-28T1059.json`): no token, no `hash=`, 0 points at 0/0.
