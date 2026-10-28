# Fotos der Weltreise 1892/93 als Kartenebene (ArcGIS Online, QGIS, StoryMaps)

Stand 27.10.2026, ca. 15:50. Erzeugt mit `analysis/ke_research/hoefer_link/ke_photos.py` im Repo `artxscience-ai/hack-the-pool-2026` (bis zum Slam privat; Team-Mitglieder haben Zugang).

## Quellen
- die Fotoliste des Teams `expedition_pool_edition/2_processing/normalization/json/bilder.json` (Stand 15:41: 408
  Weltmuseum-Fotos, Inventarnummer, Titel, Datierung, Geografie, Weltmuseum-Link);
- Höfers Reiseübersicht (`expedition_pool_edition/2_processing/analyses/itinerary_1892_93.csv`);
- die datierten Stationen in diesem Ordner (`ke_stops_dated.csv`).

**Alle Zuordnungen sind Vorschläge**, bis jemand sie geprüft hat.

## Dateien

| Datei | Inhalt |
| --- | --- |
| `ke_photos_dated.csv` | 159 Fotos mit Tagesdatum, je eine Zeile; 87 mit Koordinaten. CSV mit BOM, `date` als JJJJ-MM-TT |
| `ke_photos_dated.geojson` | die 87 Fotos mit Koordinaten (WGS84) |
| `ke_photos_summary.json` | Zählungen, Herkunft der Koordinaten, Abgleich Route ↔ Museum |

**Felder:**
- `date` (erster Tag; bei Zeiträumen `date_range = ja`), `day_index` (Tage seit 15.12.1892,
  falls ein Werkzeug Daten vor 1900 nicht liest);
- `place_of_day`: Franz Ferdinands Ort an dem Tag laut Reiseübersicht; `day_kind`
  `stay`/`travel`;
- `museum_geography` und `team_route_place` aus der Teamliste;
- `coord_source`: Station / GeoNames mit Abstand zur Route / abgelehnt / keine;
- `museum_url`: Link zur Objektseite;
- `verified_vf_match = ja`: die 21 von uns geprüften Seiten.

**Nicht enthalten:**
- die KI-Bildbeschreibungen der Teamliste („ai-assisted“, ungeprüft) und die Tier-Angaben;
- das Bild selbst. Es gibt nur den Link: Bildrecht Weltmuseum, „private Nutzung“.

## In ArcGIS Online laden (Rolle Creator nötig)

1. **Karte** öffnen, Grundkarte „Light Gray Canvas“, Beschriftungsebene ausschalten.
2. **Ebenen → Hinzufügen → Ebene aus Datei** → `ke_photos_dated.csv` → „gehostete Feature-Ebene
   erstellen“.
   - Ort aus `latitude`/`longitude` (wird erkannt).
   - Feldtyp von **`date` auf Datum** prüfen; falls Text, „Date only“ wählen.
   - Zeilen ohne Koordinaten werden nicht gezeichnet; sie stehen nur in der CSV.
3. Ebeneneigenschaften → **Zeit** aktivieren: Start = `date`. Zeitschieberegler mit Intervall
   1 Tag. Zusammen mit `ke_stops_dated` und `ke_legs` (Ordner
   `expedition_pool_edition/3_visualization/arcgis/layers/`) läuft die Reise ab, und die Fotos
   erscheinen am Tag ihrer Aufnahme.
4. **Darstellung:** einfaches Symbol (Kamera oder kleiner Kreis), **Clustering an**, weil viele
   Fotos am selben Ort liegen (z. B. 29 in Hyderabad).
5. **Pop-up:** Titel `{title}`; Felder `museum_date`, `place_of_day`, `museum_geography`; Link
   `{museum_url}` als „Objekt im Weltmuseum“. Bilder nicht einbetten.
6. Speichern, **nur in Gruppe/Organisation teilen**. „Jeder“ ist Veröffentlichung.

QGIS: `ke_photos_dated.geojson` per Drag-and-drop. Zeit über die Ebeneneigenschaften →
Zeitsteuerung, Feld `date`.

## Wie der Ort entsteht (Regeln vor dem Lauf festgelegt)

1. **Ort des Tages:** der Aufenthalt der Reiseübersicht, der das Datum umfasst. An reinen
   Reisetagen das Ziel der Etappe.
2. **Koordinaten:**
   1. eine datierte Station, deren Namen (damals, heute, gedruckt, Namensgeschichte) passen.
      Höfers eigene Klammerpaare („Haidarabad (Hyderabad)“) zählen als Schreibvariante.
   2. sonst GeoNames (Orte über 15.000 Einwohner, nur in den Ländern des Reiseabschnitts),
      **nur wenn der Treffer höchstens 400 km von einer Station liegt, die ±14 Tage um das
      Datum erreicht wurde**;
   3. sonst keine.
3. Auf diese Weise abgelehnt: „Butte City“ → Tempe, Arizona (1650 km von der Route). Ein
   früherer Lauf hatte „Katni“ (Nepal) in Katni, Indien verortet. Deshalb ist der
   Nepal-Abschnitt jetzt auf Nepal beschränkt.
4. Ohne Koordinaten bleiben 72 Fotos: kleine Orte und Lager (Kalawewa, Katni, Siriska,
   Badgery Station, Yellowstone-Hotels …). **Koordinaten von Hand setzen wir nicht**
   (Teamentscheid). Das Museum oder das Team kann sie ergänzen.

## Abgleich Route ↔ Museum (159 Fotos)

- Die Regel „derselbe Ort“ (Schreibweise und Höfers Klammerpaare) trifft bei **69** Fotos zu.
- Gelesen (Agent, Vorschlag) sind die übrigen 90 fast alle stimmig:

| Klasse | Fotos |
| --- | ---: |
| derselbe Ort, andere Schreibweise (Tjipandak/Cipandak, Mijanoschita/Miyanoshita …) | 10 |
| Museum nennt die Region (Nepal-Lager ↔ „Terai“, Siriska ↔ Alwar) | 24 |
| auf See / Reisetag („Passage New York – Le Havre, auf hoher See“ …) | 20 |
| Ausflug vom Aufenthaltsort (Badgery Station, Blue Mountains, Yellowstone …) | 26 |
| Artefakt der Tagesregel (20.1.1893 Bombay statt Tandur; Kyoto ↔ Fuji) | 7 |
| **echter Widerspruch** | **2** |
| Museumsgeografie fehlt | 1 |

**Die zwei Widersprüche, für das Museumsteam:**
- „Darbar stable“, 5.3.1893: Museum Jodhpur, Route Jaipur.
- „Heilige Messe an Bord“, 18.8.1893: Museumsgeografie VR China, Route Tokio.
