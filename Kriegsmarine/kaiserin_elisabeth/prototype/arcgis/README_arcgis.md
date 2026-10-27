# Reise 1892/93 für ArcGIS Online, StoryMaps und andere Werkzeuge

Stand 27.10.2026. `export_dated.py` (nur Python-Standardbibliothek) schreibt die Dateien in
diesem Ordner aus den Daten des Prototyps, der Reiseübersicht (`../../../Analysen/`) und den
Jagden (`../../../enrichment/`). Neu erzeugen: `python3 export_dated.py`.

Die älteren `ke_stops.*` und `ke_routes.geojson` (aus `scripts/ke_arcgis_pack.py`) bleiben
unverändert. Sie haben nur Abschnittsdaten (12.12.1892–19.12.1893 für alle Stationen) und
taugen deshalb nicht für einen Zeitschieberegler.

## Dateien

| Datei | Inhalt | Für |
| --- | --- | --- |
| `ke_stops_dated.csv` / `.geojson` | 48 Stationen Franz Ferdinands, Ankunftsdatum, Namen damals/heute, Namensgeschichte, Kulturpool | Punkte, Tour-Stationen |
| `ke_legs.geojson` | 47 Etappen als Großkreis (1°-Schritte), Yokohama → Vancouver an ±180° geteilt | Linien, Zeitschieberegler |
| `ke_hunts.csv` / `.geojson` | 12 Jagden laut Tagebuch, Tiere, Zeitraum | Punkte |
| `ke_press.csv` / `.geojson` | ANNO-Ausschnitte zu den Jagden aus `../data/presse_anno.csv` (Stand 27.10.: 69), am Ort der Jagd | Punkte, Pop-ups |
| `ke_photos_dated.csv` / `.geojson` | 159 Weltmuseum-Fotos der Reise mit Tagesdatum (aus `normalization/json/bilder.json`), am Ort des Tages laut Reiseübersicht; 87 mit Koordinaten. Nur Links zum Museum, keine Bilder. Anleitung und Regeln: `README_photos.md` | Punkte (Clustering), Zeitschieberegler |

### Wichtige Felder

- `arrival_date` (JJJJ-MM-TT): Ankunft laut Höfers Reiseübersicht, das Ende der Etappe zum Ort
  oder der Beginn des Aufenthalts.
  - `date_estimated = 1` heißt geschätzt, nämlich gleichmäßig zwischen den Nachbarstationen.
    Das betrifft 6 Stationen: Pola (Heimathafen, ohne Datum), Tjiandjur (Reihenfolge im Vault
    weicht von Höfer ab), Shimonoseki, Nagoya, Penticton, Wyoming (nicht bei Höfer).
- Die Etappe Pola → Triest hat kein Datum (das Schiff vor der Einschiffung) und wird bei
  eingeschalteter Zeit nicht gezeichnet.
- `day_index`, `day_from`, `day_to`: Tage seit 15.12.1892. Damit lässt sich filtern, falls ein
  Werkzeug die Daten vor 1900 nicht als Datum liest.
- `title` und `description`: vorbefüllt für Pop-ups und StoryMaps-Touren.
- `image_url`: nur gesetzt, wenn der Kulturpool-Datensatz offen lizenziert ist (6 Stationen:
  Public Domain oder CC0). Dazu kommen `image_title`, `image_licence` und `image_record_url`.
  - Alle anderen Stationen haben nur Titel, Lizenz und Link (`kp_example*`).
- `hoefer_from`/`hoefer_to`: erste und letzte Erwähnung bei Höfer (nicht Ankunft und Abfahrt).
- Presse `status`: **automatisch ausgewählt, ungeprüft (OCR)**. So steht es auch im Pop-up.

## Weg A: ArcGIS Online (Rolle Creator nötig)

Mit der Rolle Viewer lassen sich weder Dateien hochladen noch Karten speichern oder Stories
bauen. Vorher beim Admin die Rolle klären.

1. **Hochladen:** Content → New item → Datei wählen → "Create a hosted feature layer".
   - Punkte als **CSV** hochladen: ArcGIS liest `JJJJ-MM-TT` dann als Feldtyp "Date only".
   - Linien als **GeoJSON** (`ke_legs.geojson`).
   - Nach dem Hochladen in der Datentabelle prüfen, ob `arrival_date` ein Datumsfeld ist. Ob
     ArcGIS Daten vor 1900 richtig liest, ist noch nicht getestet. Notfalls mit `day_index`
     filtern.
2. **Karte:** Map Viewer → die vier Layer hinzufügen → Grundkarte "Modern Antique" oder
   "Vintage Shaded Relief" für den Zeitbezug.
   - Linien nach `on_ship` einfärben, `nein` gestrichelt.
3. **Zeit:** Layer-Eigenschaften → Time.
   - Stationen: Startfeld `arrival_date`.
   - Etappen: Start `date_from`, Ende `date_to`.
   - Jagden: Start `date_from`, Ende `date_to`.
   - Den Zeitschieberegler auf Tage stellen.
   - "Show features progressively" lässt die Route wachsen.
4. **Pop-ups:**
   - Titel `{title}`, dazu `{description}`.
   - Bild nur aus `{image_url}`, mit `{image_licence}` und Link `{image_record_url}`.
   - Presse: `{quote}`, `{newspaper}`, Link `{page_url}`, `{status}`.
5. **StoryMaps:** Guided map tour → Orte aus dem Layer `ke_stops_dated` übernehmen.
   - Bis 200 Orte aus einem Layer, also passen alle 48.
   - "Show progress lines" erst an der Etappe Yokohama → Vancouver prüfen.
   - Bilder verlinken statt hochladen (Hochladen kostet Credits), Feld "Attribution" mit
     Lizenz füllen, "Alternative text" schreiben.
6. **Teilen mit "Everyone" ist Veröffentlichen.** Der Builder fragt dann auch nach den Layern.

## Weg B: ohne ArcGIS-Konto

- **Die fertige Karte des Teams** (D3, alles eingebettet, offline): Grenzen 1893 ↔ heute zum
  Überblenden, Namen damals ↔ heute, Zeitschieberegler, Jagden, Presse. Sie liegt noch nicht im
  Repo, weil die Grenzen von 1893 (CShapes 2.0) CC BY-NC-SA sind.
- **kepler.gl** (läuft im Browser, die Daten bleiben lokal): CSV hineinziehen, Zeitfilter auf
  `arrival_date` legen und abspielen. Gut für die Animation, schwach für Text und Bilder.
- **uMap** (auf OpenStreetMap): GeoJSON importieren, Pop-ups aus den Feldern bauen. Geht ohne
  Konto über einen Bearbeitungslink. Keinen Zeitschieberegler.
- **QGIS:** alle Dateien hineinziehen, Zeit über "Temporal Controller", für die Präsentation
  als Bild oder Video exportieren.

## Grenzen von 1893

Sie werden hier **nicht** exportiert. CShapes 2.0 steht unter CC BY-NC-SA 4.0, und ein öffentlich
geteilter Layer wäre eine Weitergabe. Alternativen:

- In ArcGIS genügt eine historisch gestaltete Grundkarte.
- OpenHistoricalMap hat Grenzen mit Datum unter CC0 (z. B. British Raj, Ceylon, Niederländisch-
  Indien, Deutsch-Neuguinea, Neukaledonien, Qing, Japan, die australischen Kolonien).

## Quellen und Nachweise

- Reiseübersicht: Höfer (Hrsg.), *Imperial Sightseeing*, 2010, nach dem Tagebuch 1895. Nur
  Daten und Orte, kein Text.
- Namen: Linked-Places-Gazetteer des Teams (GeoNames CC BY 4.0, Wikidata CC0).
- Presse: ANNO, Österreichische Nationalbibliothek. Kulturpool: Lizenz je Datensatz.
- Fotos: Weltmuseum Wien, Fotosammlung (Bildrecht beim Museum, nur Links). Ort des Tages aus der Reiseübersicht; Koordinaten aus den Stationen oder GeoNames (CC BY 4.0), höchstens 400 km von der Route.
- Grundkarten in ArcGIS: Esri.
