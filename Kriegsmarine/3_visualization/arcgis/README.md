# Karte: SMS Kaiserin Elisabeth 1892–93 (ArcGIS, öffentlich)

[![Karte der Reise 1892–93 (ArcGIS Exhibit)](vorschau_exhibit.jpg)](https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596)

- **Tour (Exhibit):** <https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596>
- **Zeitleiste (Slider):** <https://cacgeoportal-hub.maps.arcgis.com/apps/instant/slider/index.html?appid=63327c035045432f95793e26965e0d39>
- **StoryMap „Who was hunted?“:** <https://storymaps.arcgis.com/stories/c658af3fb35b4688974d3cb214fb500b> (verlinken, nicht einbetten: siehe `EINBETTEN.md`)
- **Web-Karte:** <https://cacgeoportal-hub.maps.arcgis.com/home/item.html?id=977298da4e1a47c380c77a9041e11908>

Seit 28.10.2026 öffentlich (Karte, 8 Ebenen, beide Apps). Jede Ebene beschreibt Quelle, Methode,
Prüfstand und Rechte (Details-Panel); jedes Pop-up endet mit „Quelle · Status · Rechte“.
Daten: Team-Stand `a4b8b5a` (Tagebuchtage mit Koordinatenherkunft). Spätere Team-Änderungen
(z. B. die neue ANNO-Auswahl 57eb62e) sind noch nicht in der Karte.

## Inhalt dieses Ordners

| Pfad | Inhalt |
| --- | --- |
| `export_2026-10-28/` | Die Online-Karte als Dateien (Stand 28.10., 10:59 UTC, nach den Korrekturen unten): 8 Ebenen als GeoJSON, `webmap.json`, `items.json` (Beschreibung, Quellen, Rechte je Ebene), `layers.json`, `MANIFEST.md` mit Anzahl und SHA-256 |
| `HERKUNFT_data_provenance.md` | Herkunft je Ebene: Quelle, Methode, Prüfstand, Rechte, Zahlen (englisch; erzeugt aus `skripte/ke_sources.json`) |
| `skripte/` | Die Skripte, mit denen die Karte gebaut, geprüft und exportiert wurde (Kopie aus dem Projekt-Repo; Erklärung in `skripte/README_arcgis.md`). Die JS-Skripte laufen im Browser in einer Seite der ArcGIS-Organisation; die Python-Skripte erwarten die Ordnerstruktur des Projekt-Repos |
| `EINBETTEN.md` | **Anleitung für die Webseite**: alle Adressen, fertiger iframe-Code (responsiv), Quellenzeile, Hinweise |
| `index.html`, `vorschau_exhibit.jpg` | Einbettung und Vorschaubild |

Rechte der Daten: Fotos des Weltmuseums nur als Link und mit Lizenzhinweis je Bild (109 CC BY-NC-SA 4.0
über Europeana, die übrigen „Lizenz nicht geprüft“); Tagebuch-Zitate aus dem OCR der gemeinfreien
Ausgabe 1895; ANNO nur kurze Zitate mit Link; Höfer 2010 nur Daten und Orte.

## Einbetten

GitHub zeigt in README-Dateien keine iframes. `index.html` in diesem Ordner bettet beide Apps ein;
sie wird als Webseite sichtbar, sobald GitHub Pages für das Repo eingeschaltet ist
(Settings → Pages, nur Admins). Für jede andere Webseite:

```html
<iframe src="https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596"
  width="100%" height="600" style="border:0" allowfullscreen
  title="SMS Kaiserin Elisabeth 1892–93 (ArcGIS Exhibit)"></iframe>
```

## Korrekturen gegenüber `layers/` (28.10.)

Die Online-Karte und `export_2026-10-28/` weichen an diesen Stellen von den Dateien in `layers/`
(früher `prototype/arcgis/`) ab; dort sind sie noch nicht korrigiert:

- Station „Livingston“ lag in Livingston, New Jersey (GeoNames 5100572), jetzt Livingston, Montana
  (Punkt des Tagebuchtags 20.9.1893 aus `../web/data/ke_enrichment.js`).
- Station „Wyoming“ lag in Wyoming, Michigan (GeoNames 5015618), jetzt Yellowstone National Park
  (Wikidata Q351). Die Etappen Spokane–Livingston–Wyoming–Chicago sind neu gezogen.
- Station „Tjiandjur“: Ankunft 15.4.1893 laut Höfer statt geschätzt 6.5.1893
  (`ke_stops_dated.csv` hatte den Höfer-Wert, schätzte aber trotzdem); Etappe Buitenzorg–Tjiandjur
  beginnt am 12.4. (erster Besuch in Buitenzorg).
- Kulturpool-Suchlinks: der Parameter heißt `query`, nicht `q` (`kp_search_url`).
- Drei Abschuss-Einträge (Gwalior 30.1., Owa Raha/Ugi 8.–9.6.1893) lagen auf 0°/0°; jetzt am Punkt
  des Tagebuchtags. Ursache: `lat: 0, lon: 0` als Platzhalter für gwalior und owaraha in
  `../../2_processing/enrichment/places.json`.

Bilder der Fotos: Weltmuseum Wien; 109 mit CC BY-NC-SA 4.0 (Europeana), die übrigen mit dem Hinweis
„Lizenz nicht geprüft“.
