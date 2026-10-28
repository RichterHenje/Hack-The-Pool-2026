# Presentation: Visualisierungen Kaiserin Elisabeth

Stand 28.10.2026. Drei Seiten (HTML) und ihre Diagramme als SVG, alle mit denselben Design-Tokens.

## Dateien

| Ordner / Datei | Inhalt |
| --- | --- |
| `html/workflow_data-cleaning-and-enrichment.html` | Workflow des Data-Cleaning-Teams (englisch), mit Kartenausschnitt |
| `html/workflow_interface-team.html` | Workflow des Interface-Teams (englisch), drei Prototypen |
| `html/jagdsaetze_tiere.html` | Tierarten und zeitlicher Verlauf der Jagdsätze (deutsch) |
| `svg/workflow_data-cleaning-and-enrichment.svg` | dasselbe Diagramm als SVG |
| `svg/workflow_interface-team.svg` | dasselbe Diagramm als SVG |
| `svg/jagdsaetze_1_tierarten.svg`, `_2_zeitverlauf.svg`, `_3_tierarten_je_monat.svg` | die drei Tier-Diagramme als einzelne SVG |
| `tokens.css` | Farben und Schriften an einer Stelle, hell und dunkel |
| `scripts/` | Skripte und Vorlagen, die Kartenausschnitt, Tier-Diagramme und Workflow-Seite erzeugen |
| `visualisierungen_kaiserin_elisabeth.zip` | alles oben in einem Paket |

## Design anpassen

1. HTML: Im `:root`-Block am Anfang des `<style>` stehen die Werte aus `tokens.css`. Dort Farben und Schriften ersetzen. Alle Elemente ziehen ihre Farben aus diesen Variablen, einschließlich Dark Mode.
2. SVG: Die Farben stehen fest im `<style>`-Block jeder Datei (heller Hintergrund, kein Dark Mode). Dort dieselben Werte ersetzen.
3. Schriften: Fraunces (Titel) und IBM Plex Sans (Text) kommen von Google Fonts. Ohne Internet greifen Georgia und Segoe UI. In den SVG sind keine Schriften eingebettet. Für Druck oder Folien den Text in Illustrator oder Inkscape in Pfade umwandeln.

## Daten

- Tier-Diagramme: `kaiserin_elisabeth/prototype/data/ke_diary.json`. Gezählt werden Sätze mit „erlegen“ oder „schießen“ und die darin genannten Tierarten, keine Stückzahlen. Die Texterkennung ist ungeprüft.
- Kartenausschnitt: `prototype/arcgis/ke_routes.geojson`, `ke_stops.geojson` und die Küstenlinie `prototype/data/world.js` (Natural Earth).
- Die Skripte in `scripts/` haben absolute Pfade zum Repo am Anfang der Datei und müssen dort angepasst werden.
