# Karte: SMS Kaiserin Elisabeth 1892–93 (ArcGIS, öffentlich)

[![Karte der Reise 1892–93 (ArcGIS Exhibit)](vorschau_exhibit.jpg)](https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596)

- **Tour (Exhibit):** <https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596>
- **Zeitleiste (Slider):** <https://cacgeoportal-hub.maps.arcgis.com/apps/instant/slider/index.html?appid=63327c035045432f95793e26965e0d39>
- **Web-Karte:** <https://cacgeoportal-hub.maps.arcgis.com/home/item.html?id=977298da4e1a47c380c77a9041e11908>

Seit 28.10.2026 öffentlich (Karte, 8 Ebenen, beide Apps). Jede Ebene beschreibt Quelle, Methode,
Prüfstand und Rechte (Details-Panel); jedes Pop-up endet mit „Quelle · Status · Rechte“.
Daten: Team-Stand `a4b8b5a` (Tagebuchtage mit Koordinatenherkunft).

## Einbetten

GitHub zeigt in README-Dateien keine iframes. `index.html` in diesem Ordner bettet beide Apps ein;
sie wird als Webseite sichtbar, sobald GitHub Pages für das Repo eingeschaltet ist
(Settings → Pages, nur Admins). Für jede andere Webseite:

```html
<iframe src="https://cacgeoportal-hub.maps.arcgis.com/apps/instant/exhibit/index.html?appid=c79ee6edf2084f31b3a2f7e0be943596"
  width="100%" height="600" style="border:0" allowfullscreen
  title="SMS Kaiserin Elisabeth 1892–93 (ArcGIS Exhibit)"></iframe>
```

## Korrekturen gegenüber `prototype/arcgis/` (28.10.)

Die Karte weicht an diesen Stellen von den Dateien im Ordner `prototype/arcgis/` ab; dort sind sie
noch nicht korrigiert:

- Station „Livingston“ lag in Livingston, New Jersey (GeoNames 5100572), jetzt Livingston, Montana
  (Punkt des Tagebuchtags 20.9.1893 aus `ke_enrichment.js`).
- Station „Wyoming“ lag in Wyoming, Michigan (GeoNames 5015618), jetzt Yellowstone National Park
  (Wikidata Q351). Die Etappen Spokane–Livingston–Wyoming–Chicago sind neu gezogen.
- Station „Tjiandjur“: Ankunft 15.4.1893 laut Höfer statt geschätzt 6.5.1893
  (`ke_stops_dated.csv` hatte den Höfer-Wert, schätzte aber trotzdem); Etappe Buitenzorg–Tjiandjur
  beginnt am 12.4. (erster Besuch in Buitenzorg).
- Kulturpool-Suchlinks: der Parameter heißt `query`, nicht `q` (`kp_search_url`).
- Drei Abschuss-Einträge (Gwalior 30.1., Owa Raha/Ugi 8.–9.6.1893) lagen auf 0°/0°; jetzt am Punkt
  des Tagebuchtags.

Bilder der Fotos: Weltmuseum Wien; 109 mit CC BY-NC-SA 4.0 (Europeana), die übrigen mit dem Hinweis
„Lizenz nicht geprüft“.
