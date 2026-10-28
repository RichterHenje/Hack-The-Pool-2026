# 06 · Slam (Wed 14:00, short, all teams)

Skeleton: question → what we built → **one number** → what it means for Kulturpool → ask.

## Pitch

A ship's archive and a national aggregator describe the same voyage, and they barely meet. We placed 70 of the 90 stations of SMS Kaiserin Elisabeth on a map and asked Kulturpool what it holds for each place in the years of the voyage. Twenty-four stations have a dated record, two records name the ship, and the museums that hold the voyage are not among the portal's data providers today. The Weltmuseum photographs reached Europeana through Kulturpool in 2019, yet the portal finds no Tandur-Camp. We read the diary against the grain, day by day, with the hunting sentences, the animals, and the people in the photographs beside the route. The archive stays as it is, and the links are a sourced layer beside it that grows with every provider who connects. We ask Kulturpool and its partners to tell us which records belong to the voyage, and to connect the museums that hold it.

Claim tags (one per claim line under "Claims"; `scripts/gate_check --upto G3` fails on
an untagged line and on an empty list):

| tag | meaning |
| --- | --- |
| `MEASURED <file>` in square brackets | our own number, reproducible from the repo |
| `CITED <author year, DOI, locator>` in square brackets | checked in the source itself |
| `PROPOSED` in square brackets | interpretation or next step, said as such |

Every MEASURED claim is recomputed by `uv run python -m scripts.slam_numbers --check` (OK,
STALE, NOFILE, UNPARSED; PROBE marks a dated API, facet, or script observation that cannot be
recomputed offline).

## Claims

- The vault names 90 stations of the Kaiserin Elisabeth (1892–1914); 70 of them can be placed automatically [MEASURED prototype/data/ke_itinerary.csv]
- 24 of the 70 stations have a Kulturpool record that names the place and is dated within ±2 years of the voyage [MEASURED prototype/data/ke_stop_records.json]
- 2 Kulturpool records name the ship ("S.M.S. Kaiserin Elisabeth", phrase search 2026-10-27) [MEASURED scripts/ke_stop_records.py SHIP_QUERIES]
- Weltmuseum Wien, KHM, Heeresgeschichtliches Museum, and Staatsarchiv do not appear as data providers in today's Kulturpool portal [MEASURED docs/02_quests.md, dataProvider facet 2026-10-27]
- The Weltmuseum photographs of the voyage have been in Europeana since 2019, delivered through Kulturpool as aggregator, licence CC BY-NC-SA 4.0 [CITED Europeana API record 15504/VF_14687: edmProvider Kulturpool (org 3053), edmDataProvider Weltmuseum Wien (org 1628), edmRights CC BY-NC-SA 4.0, timestamp_created 2019-07-05, gelesen 2026-10-28]
- A search for "Tandur-Camp" in the Kulturpool portal finds no record today [MEASURED kp.kulturpool.search 2026-10-28]
- 131 of the 134 Europeana photographs of the voyage (the team's list) are CC BY-NC-SA 4.0; 58 of them lie on our map [MEASURED scripts/arcgis/ke_photos_rights.js, ke_enrichment.js photos.rights]
- The team's page shows the diary of the voyage as 309 days, 14 December 1892 to 18 October 1893; the demo day, 11 January 1893 at Kalawewa (Ceylon), has its own heading in the diary on scan 75 [CITED reference/team-khm at b5e1464, Kriegsmarine/normalization/json/tagebuch_tage.json, days 1892-12-14 to 1893-10-18, entry 1893-01-11 method heading, scan 75; read 2026-10-28]
- Hits name the place, not the voyage ("Colombo" also finds Columbus) [PROPOSED]
- An archive stays as it is; links are a separate, sourced layer beside it [PROPOSED] (principle after FastCat/Elicit G0; the original is not checked, so not CITED)

## Retired claims

German originals of 27.10. and 28.10. 00:49, kept verbatim; each points at its English claim above or names why it left the list.

- Der Vault nennt 90 Stationen der Kaiserin Elisabeth (1892–1914); 70 davon lassen sich automatisch verorten [MEASURED prototype/data/ke_itinerary.csv] (translated: see claim 1)
- 24 der 70 Stationen haben einen Kulturpool-Datensatz, der den Ort nennt und in die Jahre der Reise ±2 datiert ist [MEASURED prototype/data/ke_stop_records.json] (translated: see claim 2)
- 2 Kulturpool-Datensätze nennen das Schiff mit Namen („S.M.S. Kaiserin Elisabeth“, Phrasensuche 2026-10-27) [MEASURED scripts/ke_stop_records.py SHIP_QUERIES] (translated: see claim 3)
- 202 der 589 Einträge im Vault (34 %) kommen im Kulturpool-Text nicht vor [MEASURED analysis/vault_vs_kulturpool.csv] (retired: counted on the vault of 27.10. 10:20, before the team's vault clean-up; the file still reproduces the number, the recount on the cleaned vault is deferred to the morning)
- Weltmuseum Wien, KHM, Heeresgeschichtliches Museum und Staatsarchiv erscheinen im heutigen Kulturpool-Portal nicht als Datengeber [MEASURED docs/02_quests.md, dataProvider facet 2026-10-27] (translated: see claim 4)
- Die Weltmuseum-Fotos der Reise stehen seit 2019 in Europeana, geliefert über den Kulturpool als Aggregator, Lizenz CC BY-NC-SA 4.0 [CITED Europeana API record 15504/VF_14687: edmProvider Kulturpool (org 3053), edmDataProvider Weltmuseum Wien (org 1628), edmRights CC BY-NC-SA 4.0, timestamp_created 2019-07-05, gelesen 2026-10-28] (translated: see claim 5)
- Im Kulturpool-Portal findet die Suche „Tandur-Camp“ heute keinen Treffer [MEASURED kp.kulturpool.search 2026-10-28] (translated: see claim 6)
- 131 der 134 Europeana-Fotos der Reise (Liste des Teams) sind CC BY-NC-SA 4.0, 58 davon liegen auf unserer Karte [MEASURED scripts/arcgis/ke_photos_rights.js, ke_enrichment.js photos.rights] (translated: see claim 7)
- Treffer nennen den Ort, sie stammen nicht von der Reise („Colombo“ findet auch Kolumbus) [PROPOSED] (translated: see claim 9)
- Ein Archiv bleibt, wie es ist; Verknüpfungen sind eine eigene, belegte Schicht daneben [PROPOSED] (Prinzip nach FastCat/Elicit G0; das Original ist nicht geprüft, daher nicht CITED) (translated: see claim 10)
