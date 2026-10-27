# Normalisierung: Weltreise Franz Ferdinands 1892/93

Eingang ist das Team-Material in `../Vault/` und `../Sources/`; beides wird nur gelesen. Ergebnis sind
JSON-Dateien in `json/`, auf denen die Anreicherung (`../enrichment/`) aufsetzt.

```bash
python3 filter_voyage.py   # Vault  -> json/weltreise, ortschaften, personen, schiffe, sammlungen_projekte
python3 diary_days.py      # Tagebuch (OCR) -> json/tagebuch_tage.json
```

Nur Python-Standardbibliothek. `diary_days.py` lädt beim ersten Lauf die Tagesliste von
franzferdinandsworld.com in `.cache/` (nicht im Repo).

## `filter_voyage.py` (Lisa Gollner)

Filtert aus dem Vault alle Einträge zur Weltreise auf der „Kaiserin Elisabeth“ und schreibt sie in der
Struktur der `0_Muster_*`-Vorlagen; fehlende Werte sind `"NA"`, `_meta` enthält Datei, Vault-`id`
(aus den YAML-Eigenschaften) und den Auswahlgrund. Auswahlkriterien stehen im Kopf des Skripts.

| Datei | Inhalt |
| --- | --- |
| `weltreise.json` | die Reise: Beschreibung, Schiff, Besatzung laut Eintrag, Route (Ortsnotizen in Reihenfolge) |
| `ortschaften.json` | 49 Ortsnotizen der Route mit Position(en) auf der Route |
| `personen.json` | 43 Personen (Seereise-Denkmünze oder im Weltreise-Eintrag genannt) |
| `schiffe.json`, `sammlungen_projekte.json` | das Schiff (nur diese Reise), verlinkte Sammlungen |

## `diary_days.py`: das Tagebuch nach Tagen

Die OCR des gedruckten Tagebuchs (*Tagebuch meiner Reise um die Erde*, 1895/96) hat viele
Tagesüberschriften im Fließtext verstümmelt („Sikandarabad -■ Gwali . umi 28, Jännei“). Die
Markdown-Fassung in `../Sources/` kennt deshalb nur 170 Einträge; das Buch hat rund 284 Tage, ein
Eintrag umfasst oft mehrere Tage.

- Referenz für die Tage ist franzferdinandsworld.com: jeder Tag 14.12.1892–18.10.1893 mit Ort,
  284 mit eigener Seite (englische Übersetzung). Gespeichert werden nur Datum und Ort der Website.
- Die erkannten Überschriften bleiben Anker. Innerhalb eines Eintrags wird jeder deutsche Satz
  monoton einem Tag zugeordnet; Punkte gibt es für gemeinsame Eigennamen und Zahlen mit dem
  englischen Tagestext und für verstümmelte Überschriften mit passendem Monat (sie setzen die Grenze).
- Prüfung: 11 Testsätze und die 18 Tagebuch-Zitate der Tierliste (`../enrichment/heroes.json`), deren Tag
  wir aus der Website-Übersetzung kennen (teils dieselben Stellen), landen alle am richtigen Tag. Wo eine Überschrift ganz in der OCR fehlt, kann die Grenze um ein bis
  zwei Sätze danebenliegen (z. B. Ankunft in Gwalior am 29. Jänner).
- Seiten, die in der OCR fehlen (z. B. 31. März, 15. Juli), fehlen auch hier.

`tagebuch_tage.json`: `days[]` mit `date`, `place_site` (Ort laut Website), `heading_ocr` und
`entry_date` (Eintrag in der OCR), `band`, `scan`, `page_url` (Internet Archive), `site_url`,
`method` (`heading` | `aligned` | `no_entry`), `text` (OCR, unkorrigiert).
