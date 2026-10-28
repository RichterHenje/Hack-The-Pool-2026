# Workflow: Data Cleaning and Enrichment, Fassung 2

Stand 28.10.2026. Überarbeitete Kopie von `../svg/workflow_data-cleaning-and-enrichment.svg`
und `../html/workflow_data-cleaning-and-enrichment.html`; die ursprüngliche Fassung bleibt unverändert.

| Datei | Inhalt |
| --- | --- |
| `svg/workflow_data-cleaning-and-enrichment.svg` | Diagramm als SVG |
| `html/workflow_data-cleaning-and-enrichment.html` | dasselbe Diagramm als Seite, mit Kartenausschnitt |

## Änderungen gegenüber `presentation/`

- **2 · Structure diary and rank lists:** „Extract days, places, hunts“ aufgeteilt in „Split diary into 309 days“
  und „Extract places, hunts“; „Cross-check with Höfer“ → „Cross-check: Höfer, day list“ (Tagesliste von franzferdinandsworld.com, im Diagramm nicht eigens genannt).
- **4 · Enrichment:** „Wikidata“ → „Wikidata, GND“ (Normdaten, Koordinaten); GeoNames nur noch für Koordinaten
  aus den Tagebuch-Überschriften; Europeana liefert Fotos der Reise, keine Objekte.

Gründe: Die Tage und Ortsnamen stammen aus der Tagesliste von franzferdinandsworld.com
(`normalization/diary_days.py`); die meisten Koordinaten kommen aus Wikidata, GeoNames nur für 54 der 216 verorteten Tage;
Europeana liefert 134 Fotos der Reisefotografen (`enrichment/data/europeana.json`).
