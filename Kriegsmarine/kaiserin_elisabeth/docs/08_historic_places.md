# 08 · Historic place names (best practice, run 2026-10-27)

## The standard: Linked Places Format (LPF)

The World Historical Gazetteer (WHG) and Pelagios use **Linked Places Format** (GeoJSON-LD,
spec: github.com/LinkedPasts/linked-places-format). One Feature per place; `names[]` holds
every toponym with `lang`, `citations[]` and an optional `when` (timespans); `links[]`
holds `closeMatch` / `exactMatch` to GeoNames, Wikidata, GND, Getty TGN. Our file is
validated against WHG's own schema (`reference/lpf/schema_lpf_v1.2.2.json`, from
github.com/WorldHistoricalGazetteer/whg3). The check can fail: five deliberately broken
records (no title, no names, bad link type, 3-letter country code, timespan without
start) were all rejected.

## Attestation is not validity

| kind (in each name's citation label) | meaning | `when` |
| --- | --- | --- |
| `attested` | the source (team vault) wrote this name for this voyage: "Bombay", "Batavia", "Tsingtau", "Pola" | voyage years: **when it was used**, not when it was valid |
| `historic` | GeoNames alternate name flagged historic | from/to if GeoNames gives them |
| `dated` | GeoNames alternate name with from/to | validity |
| `official` | Wikidata P1448 official name with P580/P582 | validity |
| `current` / `label` | GeoNames name; Wikidata labels | none |

Only the period name counts as attested: "Bombay (Indien, Heut. Mumbai)" attests
*Bombay*; the vault adds *Mumbai* as a modern gloss.

## Run (`uv run python -m scripts.ke_places_lpf`)

Input: the 59 geocoded places of the SMS Kaiserin Elisabeth itinerary
(`scripts/ke_itinerary.py`). Output: `prototype/data/ke_places.lpf.json`.

| | n |
| --- | ---: |
| places | 59 |
| with a Wikidata item (via GeoNames id P1566) | 56 |
| with a GeoNames name flagged historic | 13 |
| with any dated validity (GeoNames from/to or Wikidata P580/P582) | 11 |
| schema errors | 0 |

Examples: Batavia (en) 1619-1949, Djakarta 1949-1972, Jakarta from 1972; Bombay until
1995, Mumbai from 1995; Pola (it) / Pula (hr); Tsingtau (de) historic for Qingdao.

Sources: GeoNames alternate names per country (`download.geonames.org/export/dump/
alternatenames/<CC>.zip`, CC BY 4.0; colloquial names excluded) and one batched SPARQL
query to query.wikidata.org (CC0). Several Wikidata items can claim one GeoNames id
(Shanghai's id was also claimed by a hospital): items are kept apart and the one whose
label matches the GeoNames name is used.

## Use: period-correct searching (`kp.places.query_names`)

For a place and a time window, search the attested names plus Latin-script names whose
validity overlaps the window (undated names stay in). For 1890-1895 Batavia searches
"Batavia" only (Jakarta from 1972 is out); Bombay searches "Bombay", not "Mumbai".
Tests: `tests/test_places.py` (boundary cases of the overlap rule).

**Measured effect on Kulturpool** (70 itinerary stops, segment years ±2):
before 24 stops with at least one record, 994 hits (largest single-name count per stop);
after 24 and 994. Of 28 newly added (name, window) pairs searched on their own, one has
a hit ("Kalkutta", the 1891 Census of India, already found as "Calcutta"). So Kulturpool's
records for these ports and years already use the names the vault gives. The gazetteer's
value is correctness (no anachronisms), dated names with sources, links, and a file other
gazetteers can take, not more Kulturpool hits.

## Next (not done)

- **WHG reconciliation**: upload `ke_places.lpf.json` at whgazetteer.org (browser; WHG
  blocks scripts) to reconcile against its union index and get TGN/WHG ids.
- **Getty TGN** (strongest historic-name source, with dates): SPARQL returned 499 today.
- **The 19 unmatched stops** are small places (Miyajima, Banff, Kala Wewa), not a historic-
  name problem: the full GeoNames country dumps (not only cities >15k) or a hand-checked
  coordinates table would resolve most.
- Remaining noise: undated antique names (Lutetia for Paris) and odd variants (Aebura for
  New York) pass the filter; they find nothing in a 1890s window but should be dropped
  by a name-type rule if the list is shown to users.
