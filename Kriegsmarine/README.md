# Kriegsmarine: S.M.S. Kaiserin Elisabeth und die Weltreise Franz Ferdinands 1892/93

Hackathon-Material des KHM-Teams (Hack The Pool 2026).

| Ordner | Inhalt |
| --- | --- |
| `Vault/` | Obsidian-Vault „Archive_Indien_Schiffreisen“ (Personen, Orte, Schiffe, Sammlungen), Grundlage des Teams |
| `Sources/` | Quellen: Tagebuch Franz Ferdinands (OCR, 2 Bände), Ranglisten 1892/93 |
| `normalization/` | Vault und Quellen → normalisierte JSON-Dateien (`json/`): Reise, Orte, Personen, Tagebuch nach Tagen |
| `enrichment/` | baut auf `normalization/json` auf und ergänzt externe Quellen: Wikidata, GND (lobid), ANNO, Kulturpool, Höfer 2010, Weltmuseum/Commons, franzferdinandsworld.com |
| `kaiserin_elisabeth/` | Prototyp (Karte, Reise Tag für Tag), Analysen zu Vault und Kulturpool, Datenmodell-Vorschlag |
| `Analysen/` | Höfers Reiseübersicht 1892/93, Abgleich mit dem Tagebuch, VF-Fotonummern (Weltmuseum), ANNO-Presse je Etappe |

Datenfluss: `Vault/`, `Sources/` → `normalization/` → `enrichment/` → Web-App / Prototyp.
Vault und Quellen werden von den Skripten nur gelesen.

## Hinweis: `kaiserin_elisabeth/prototype/data/ke_diary.json` ist veraltet

`kaiserin_elisabeth/scripts/ke_diary.py` teilt das Tagebuch an den 170 Überschriften, die die OCR
erkannt hat. Das gedruckte Tagebuch hat aber rund 284 Tage: 63 dieser Einträge umfassen mehrere Tage
(zusammen 113 Tage), weil die OCR die Tagesüberschriften im Fließtext verstümmelt hat. Daraus folgt
für `ke_diary.json` (und die abgeleiteten `ke_diary.csv`, `ke_diary.js`):

- Ort, Jagdsätze und Tiere eines Eintrags stehen beim ersten Tag des Eintrags; sie können 1–5 Tage
  zu früh datiert sein (z. B. Kauf der Affen in Singapur: 5. statt 8. April).
- Neun Überschriften ohne Ortsangabe (z. B. 26. Jänner) sind im Vorgängereintrag aufgegangen.
- Die Pressestimmen in `presse_anno.csv` tragen ein `event_date` nach Tagen; fällt es auf einen Tag,
  den `ke_diary.json` nicht kennt, zeigt `reise.html` sie beim davor liegenden Eintrag.

Die korrigierte Fassung ist `normalization/json/tagebuch_tage.json` (Tag, Ort, OCR-Text, Scan;
Verfahren in `normalization/README.md`). Vorschlag: `ke_diary.py` liest künftig diese Datei statt der
Überschriften in `Sources/`. Bis dahin bitte Tagesdaten aus `ke_diary.json` nicht ungeprüft übernehmen.
