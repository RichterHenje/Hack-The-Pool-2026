# ANNO-Presse: Zeitungsmeldungen zur Reise 1892/93

Stand 27.10.2026. Sucht in **ANNO** (AustriaN Newspapers Online, Österreichische
Nationalbibliothek) nach Meldungen über die SMS Kaiserin Elisabeth und Franz Ferdinands Reise
und ordnet jede Ausgabe der Etappe der Reiseübersicht zu (`../itinerary_1892_93.csv`).

**Das sind Kandidaten, keine Pressestimmen.** Die Texte sind OCR aus Fraktur, mit Lesefehlern,
und viele Treffer meinen etwas anderes (die Kaiserin, den russischen Thronfolger, das
Kaiserin-Elisabeth-Spital). Was zitiert wird, entscheidet ein Mensch am Scan.

## Lauf vom 27.10.2026

- 3 Begriffe × 11 Monate (1892-12 bis 1893-10), Obergrenze 200 Ausgaben je Begriff und Monat;
  keine Obergrenze erreicht.
- 1.382 Ausgaben, 4.789 Ausschnitte in `candidates.csv`.
- 229 Ausschnitte ohne Etappe: alle vom 1. bis 14.12.1892, also vor der Abfahrt.
- Ungeprüft. Eine Auswahl von 68 Ausschnitten zu den Jagden (Pipeline `../../enrichment/`)
  steht in `../../../3_visualization/web/data/presse_anno.csv`.

## Aufruf

Nur Python 3 (Standardbibliothek), keine Installation, kein Schlüssel. Aus diesem Ordner:

```
python3 anno_search.py                                  # alle Begriffe, 1892-12 bis 1893-10
python3 anno_search.py --months 1893-01:1893-02 --max-docs 20
python3 anno_search.py --no-snippets                    # nur Ausgaben, ohne Textausschnitte
python3 -m unittest test_anno_search                    # Tests, ohne Netz
```

- Suchbegriffe stehen in `terms.txt`, einer je Zeile, Syntax wie auf
  https://anno.onb.ac.at/anno-suche.
- Antworten werden in `cache/` gespeichert (nicht im Repo), ein zweiter Lauf geht schnell.
- Das Skript fragt der Reihe nach, mit 1 s Pause.

## Dateien

| Datei | Inhalt |
| --- | --- |
| `anno_search.py` | Client für die ANNO-Suche (`/anno-suche/rest/search/complex` und `/snippet`) |
| `terms.txt` | Suchbegriffe |
| `candidates.csv` | eine Zeile je Textausschnitt (Ausgabe × Seite × Treffer) |
| `summary.json` | Treffer je Begriff und Monat, Zahl der Ausgaben und Zeilen |
| `test_anno_search.py` | Tests ohne Netz |

Spalten von `candidates.csv`: die ersten sieben wie `presse_anno.csv` im Prototyp (`date`,
`newspaper`, `page_url`, `place`, `quote`, `voice`, `added_by`). Eine geprüfte Zeile kann so
direkt übernommen werden, `voice` und `added_by` füllt, wer sie prüft. Danach: `query`, `doc_id`,
`page`, `hits_in_doc`, `itinerary_leg`, `days_after_leg_start`.

## Wie die Zuordnung funktioniert

- Jede Ausgabe bekommt die **zuletzt begonnene Etappe** der Reiseübersicht, wenn diese
  höchstens 21 Tage vor dem Erscheinen endete (`--lag`).
  - Meldungen per Telegraf kamen nach Tagen, Briefe aus Asien oder Australien nach Wochen.
  - Die Etappe ist also ein Vorschlag, worüber die Zeitung berichtet haben könnte.
- `place` ist der Aufenthaltsort oder das Ziel dieser Etappe, nicht der Ort im Artikel.
- Ausgaben vor dem 15.12.1892 haben keine Etappe. Sie bleiben in der Liste: Ankündigungen der
  Reise.

## Was das Skript prüft

- **Monatsfilter:** Die API verwirft ein falsch geschriebenes Datum (`18921215`, `15.12.1892`)
  ohne Fehlermeldung und sucht dann über alle Jahre. Nur `JJJJ-MM` wirkt. Liegt ein Treffer
  außerhalb des angefragten Monats, bricht das Skript ab.
- **Obergrenze:** Mehr als `--max-docs` Ausgaben je Begriff und Monat werden nicht geholt.
  `summary.json` zeigt mit `capped`, wo das passiert ist.
- **Keine Bild-URLs:** Die Ausschnitte haben Bildlinks mit einem kurzlebigen `hash=`-Token. Die
  werden nicht gespeichert, nur die Seitenlinks (`page_url`, `…&seite=N`).

## Scans ansehen

`page_url` öffnet die Seite im ANNO-Viewer. Der Viewer verlangt eine Sicherheitsprüfung
(Cloudflare Turnstile): Im Browser läuft sie von selbst durch, Skripte kommen nicht an die
Seiten. Darum kommen Text und Treffer aus der Such-API, die Prüfung am Scan macht ein Mensch.

## Rechte und Herkunft

- Zeitungen von 1892/93 sind gemeinfrei. Quelle: ANNO, Österreichische Nationalbibliothek,
  https://anno.onb.ac.at/.
- Bei jedem Zitat Zeitung, Datum und Seitenlink angeben.
- Die Ausschnitte sind ungeprüfte OCR.
