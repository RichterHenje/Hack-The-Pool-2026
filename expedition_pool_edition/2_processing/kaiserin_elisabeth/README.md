# SMS Kaiserin Elisabeth 1892–1914 · Prototyp

Das Schiff als Kern: seine Reisen aus dem Vault `../../1_sources/Vault/Archive_Indien_Schiffreisen`, die
Weltreise 1892–93 Tag für Tag aus Franz Ferdinands Tagebuch (`../../1_sources/Sources/`), dazu
Kulturpool-Datensätze, Jagdstellen im Wortlaut und Pressestimmen. Vault und Quellen werden
nur gelesen und nicht verändert.

## Ansehen

Direkt im Browser öffnen (ohne Server; `reise.html` lädt als Hintergrund Kartenkacheln von Map Warper, siehe unten):

| Seite | was |
| --- | --- |
| `../../3_visualization/web/reise.html` | **Weltreise 1892–93 Tag für Tag**: Route nach dem Tagebuch, Tageskarten mit Scan-Link, Ebene „Jagd“ (Sätze vom Erlegen/Schießen im Wortlaut), Kulturpool, Presse (ANNO). Direktlink zu einem Tag: `reise.html#1893-01-11` |
| `../../3_visualization/web/geschichte.html` | **Jagdreise 1892–93 als Geschichte**: nur die Fahrt mit S.M.S. Kaiserin Elisabeth bis Yokohama (24.8.1893), in Kapiteln entlang der 18 Jagden und der Strecken dazwischen; großer Text mit Foto, Tagebuch-Zitaten, Presse, lebenden Tieren und Objekten, kleine Karte (Karte 1872) und einzeilige Zeitleiste. Die 55 Tage danach (ohne das Schiff) nur als Epilog und graue Linie. Gleiche Daten wie `reise.html` (`data/ke_enrichment.js`). Direktlink zu einem Kapitel: `geschichte.html#hunt-1893-03-09-nepal` |
| `../../3_visualization/web/index.html` | **Startseite**: wie die Daten entstanden (Quellen, Normalisierung, Anreicherung, Prüfung; Zahlen live aus `data/ke_enrichment.js`), drei Ansichten als Kacheln mit Vorschau (`img/previews/`: Geschichte, Reise Tag für Tag, offene Daten in ArcGIS), Leiste „Hack the Pool 2026“ mit Kulturpool, ACDH-CH (ÖAW) und CLARIAH-AT, Institutionen mit Logos, Literatur (Tagebuch, Höfer 2010) (`img/logos/`: Kulturpool, ÖNB, Weltmuseum Wien, Europeana, CLARIAH-AT von deren Websites, ACDH-CH von Wikimedia Commons unter CC BY-SA 4.0; Marken der Institutionen), Team, Grenzen. Die ArcGIS-Kachel verlinkt Leanders Karte in ArcGIS Online (https://cacgeoportal-hub.maps.arcgis.com/home/item.html?id=977298da4e1a47c380c77a9041e11908#overview), die StoryMap „Who was hunted?“ steht im Hinweis darunter |
| `../../3_visualization/web/schiff.html` | erster Prototyp (früher `index.html`): alle Reisen des Schiffs 1892–1914 aus dem Vault, Kulturpool-Treffer je Station. Direktlink: `schiff.html#stop=Bombay` |

## Was die Daten zeigen (Stand 27.10.2026)

| | |
| --- | --- |
| Tagebuchtage (14.12.1892–18.10.1893) | 309 (nach `../normalization/json/tagebuch_tage.json`), davon 170 mit eigener Überschrift in der OCR; 79 Überschrift-Orte im Ortsverzeichnis gefunden |
| Tage mit Sätzen vom Erlegen oder Schießen | 65 Tage, 211 Sätze (ungeprüft; genannte Tiere ≠ getötete Tiere) |
| Stationen aller Reisen 1892–1914 (Vault) | 90, davon 70 verortet; 24 mit Kulturpool-Treffern im Zeitfenster |
| Kulturpool-Datensätze, die das Schiff nennen | 2 (Phrasensuche) |
| Vault-Einträge, die im Kulturpool-Text fehlen | 202 von 589 |

**Kontext im Kulturpool** (`analysis/ke_kulturpool_kontext.md`): Intendanzakten des NHM
nennen das Schiff (Z.196/1893: Zoologe Lorenz an Bord, zurückgeschickt) und belegen die
Präparatoren Gebr. Hodek (Jagdtrophäen Kronprinz Rudolfs, Raubvögel); Marine-Weltreisen als
Sammelreisen (Fasana, Saida); Führer durch die Sammlungen von der Weltreise (1894).
Nicht Kulturpool-Partner: KHM, Weltmuseum, HGM, Schönbrunn (Schloss, Tiergarten).

## Historische Karte in `reise.html`

Hintergrund ist die Weltkarte von 1872 („World On Mercator's Projection“,
[Map Warper 98512](https://mapwarper.net/maps/98512)), abschaltbar unter „Ebenen“ (dann
Natural-Earth-Küsten). Die Karte ist ungleichmäßig georeferenziert (Ägypten passt, Mitteleuropa
rund 3° zu weit südlich, Indien und Java 2–5° zu weit nördlich, Japan rund 2° zu weit südlich).
Sie wird daher nicht verschoben; stattdessen stehen die Orte, solange sie eingeschaltet ist, dort,
wo die Karte sie zeigt: `../../3_visualization/web/data/ke_places_1872.js` (von der Seite gelesen) und
`ke_places_1872.json` (gleicher Inhalt), je Ort `lat`, `lon`, `quelle`, für Orte außerhalb des
Ortsverzeichnisses zusätzlich `heute` (heutige Koordinaten). Die Originalkoordinaten bleiben unverändert.

- Ermittelt 27.10.2026: Küstenorte per Abgleich der Kacheln (Zoom 4) mit Natural-Earth-Küsten;
  Binnenorte und schwache Treffer (Indien, China, Sydney, Aden, Triest/Pola, Pazifik) auf Zoom 6
  am Ortspunkt oder relativ zu Nachbarorten der Karte gesetzt (`quelle: Sichtprüfung …`); Banff,
  Yellowstone und US-Binnenorte geschätzt.
- Bekannter Datenfehler (nicht in dieser Datei): das Ortsverzeichnis legt „Livingston, Montana“
  nach New Jersey (`ke_enrichment.js` → `geonames`), zwei Reisetage springen daher an die Ostküste.
- Nachjustieren: `reise.html?kalibrieren`, Marker auf den Ort in der Karte ziehen, das JSON aus
  dem Textfeld in beide Dateien übernehmen.
- Schlüssel sind die Ortsnamen aus `ke_diary.json` (GeoNames). `reise.html` nutzt inzwischen die 309 Tage
  aus `normalization/json/tagebuch_tage.json` mit Wikidata-Koordinaten (Bündel `data/ke_enrichment.js`,
  `../enrichment/08_export_prototype.py`); jeder Punkt (Route, Jagden, Fotos, Tiere) wird daher wie der
  nächstgelegene kalibrierte Ort verschoben (bis 4°, Bezugskoordinaten in `ke_enrichment.js` → `geonames`
  oder `heute`). Derzeit hat jeder Tag mit Ort einen solchen Bezugsort.
- Für die Karte nennt Map Warper keine Lizenz und keine Quelle; vor öffentlicher Nutzung klären.

## Mitmachen: Presse aus ANNO

Ausschnitte von Hand in `../../3_visualization/web/data/presse_anno.csv` eintragen
(`date,newspaper,page_url,place,quote,voice,added_by`), dann
`uv run python -m scripts.ke_diary` – die Tageskarten zeigen sie (± 3 Tage).

## Neu erzeugen

Python 3.13, [uv](https://docs.astral.sh/uv/), im Ordner `expedition_pool_edition/2_processing/kaiserin_elisabeth/`:

```
uv run python -m scripts.ke_diary           # Tagebuch nach Tagen (aus ../normalization) -> Tagesroute, Jagdsätze, Presse
uv run python -m scripts.ke_itinerary       # Reisen aus dem Vault -> Stationen, Linien (schiff.html)
uv run python -m scripts.ke_places_lpf      # historische Ortsnamen (Linked Places)
uv run python -m scripts.ke_stop_records    # Kulturpool-Treffer je Station (schiff.html)
uv run python -m scripts.ke_related         # thematische Kulturpool-Suche -> analysis/
uv run python -m scripts.ke_arcgis_pack     # Layer für ArcGIS Online
uv run python -m scripts.vault_review       # Auffälligkeiten im Vault
uv run python -m scripts.vault_clean ../../1_sources/Vault/Archive_Indien_Schiffreisen --report data/clean.json   # Bereinigung (ändert Dateien! nur auf einer Kopie/Branch)
uv run --group dev pytest -q
```

Datenstand: Vault `c76376a` (schiff.html), Tagebuch-Quellen `7ccdfa9` (reise.html).
Das Ortsverzeichnis (GeoNames) wird beim ersten Lauf nach `data/` geladen (nicht im Repo).

## Inhalt

| Pfad | was |
| --- | --- |
| `../../3_visualization/web/` | die Webseiten (früher `prototype/` in diesem Ordner), Daten, Küstenlinien (Natural Earth); die Ebenen für ArcGIS Online liegen in `../../3_visualization/arcgis/layers/` |
| `kp/` | Kulturpool-API, Ortsverzeichnis (mit Länderbereich je Reiseabschnitt), historische Namen, Rechte |
| `scripts/` | die Schritte oben |
| `analysis/` | Kulturpool-Kontext, Abgleich Vault ↔ Kulturpool, Auffälligkeiten im Vault |
| `docs/08_historic_places.md` | historische Ortsnamen: Linked Places Format, Beleg vs. Gültigkeit |
| `docs/09_vault_model.md` | Vorschlag Datenmodell, Automatisierung vs. Fachleute, Formate (LIDO, EDM, Wikidata, RDF, CIDOC CRM) |
| `docs/10_vault_cleaning.md` | automatische Vault-Bereinigung als Vorschlag (Branch `khm-team-vault-cleanup`): Regeln, zwei Blindtests mit je 32 eingepflanzten Fehlern (32/32), Ergebnis |

## Grenzen

- Tagebuchtext aus der automatischen Texterkennung; Zitate am Scan prüfen.
- „Jagd“ sind Sätze mit erlegen/schießen; „Strecke“ wird nicht gezählt (heißt im Tagebuch meist Entfernung).
- Orte nur aus den Ländern des jeweiligen Reiseabschnitts; kleine Orte bleiben ohne Koordinate.
- Kulturpool-Treffer je Station nennen den Ort in den Jahren der Reise; sie stammen nicht von der Reise.
- Bilder nur bei offenen Rechten; sonst Titel, Lizenz, Link.
- Das Tagebuch ist die Stimme des Erzherzogs. Andere Perspektiven (Begleiter, Mannschaft,
  lokale Akteure, Tiere) kommen als eigene Ebenen dazu, soweit Quellen vorliegen.

## Quellen und Lizenzen

Vault und Quellen des Teams · Franz Ferdinand, *Tagebuch meiner Reise um die Erde* (1895/96,
gemeinfrei, Internet Archive) · Kulturpool API v2 (Rechte je Datensatz) · GeoNames (CC BY 4.0) ·
Wikidata (CC0) · Natural Earth (gemeinfrei) · Leaflet (BSD-2-Clause).

**Lizenz dieses Ordners: vom Team zu entscheiden.**
