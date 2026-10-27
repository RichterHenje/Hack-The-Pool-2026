# Normalisierung: Weltreise Franz Ferdinands 1892/93

Eingang ist das Team-Material in `../Vault/` und `../Sources/`; beides wird nur gelesen. Ergebnis sind
JSON-Dateien in `json/`, auf denen die Anreicherung (`../enrichment/`) aufsetzt.

```bash
python3 filter_voyage.py   # Vault  -> json/weltreise, ortschaften, personen, schiffe, sammlungen_projekte
python3 diary_days.py      # Tagebuch (OCR) -> json/tagebuch_tage.json
python3 people_voyage.py   # alle Personen der Reise -> json/personen_reise.json (nach filter_voyage.py)
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

## `people_voyage.py`: alle Personen der Reise

`filter_voyage.py` wählt Personen über die Seereise-Denkmünze bzw. die Besatzung im Weltreise-Eintrag
(43). `people_voyage.py` ergänzt – mit Code und Objektstruktur aus `filter_voyage.py`, das unverändert
bleibt – zu 64 Personen:

- **Besatzung laut Rangliste**: alle Einträge der Ranglisten 15.11.1892–1.9.1893
  (`../Sources/Ranglisten/kaiserin_elisabeth_ranglisten.csv`), zugeordnet zur Vault-Notiz (Nachname +
  erster Vorname, Titel und Partikel ignoriert); Dienstgrade stehen unter `_reise.ranglisten`.
- **Begleitung, Wissenschaft, Gastgeber** laut Tagebuch (kuratierte Liste im Skript): Clam-Martinic,
  Wurmbrand-Stuppach, Kinsky, Prónay; Lorenz von Liburnau; Havelock, Pirie, Stockinger, Imhof.
- **ohne Vault-Notiz**: Tierwärter Biaggio, Jagdbegleiter Bedford (Neuguinea).

Nichts wird zusammengeführt. `_reise.vermutlich_dieselbe_wie` markiert Ranglisten-Namen, die einer
Notiz unter anderer Schreibweise zugeordnet wurden; `_reise.moegliche_dublette` markiert Notizen mit
fast gleichem Namen (Hermann/Herrmann, Hugo; Podhorsky/Podhorszky).

## `bilder.json`: Fotos der Weltreise im Weltmuseum Wien

Nicht aus dem Vault, sondern außerhalb des Repos aus TMS (Fotosammlung VF) erzeugt; das Skript liegt
nicht im Repo. Auswahl: VF-Objekte mit „Weltreise 1892-1893“ in der Beschreibung, die Erinnerungsfotos
„Kaiserin Elisabeth“ (Pola 1894), mit Franz Ferdinand verknüpfte Fotos von 1892/93 sowie Fotos von
Eduard Hodek jun. Enthalten sind nur die **408 Bilder, die auf weltmuseumwien.at online sind**
(Objekt und Bild freigegeben); von insgesamt 2.029 Fotos sind die übrigen nicht öffentlich.

- Felder: `Datei`, `Inventarnummer`, `Titel`, `Datierung` (wie im Museum), `Geografie`,
  `Geografie-Pfad`, `Ortschaft (Route)`, `Weltmuseum-Link` (Objektseite), `Bild-Link` (das JPEG direkt,
  `https://www.weltmuseumwien.at/pics/<Objekt-ID>/<Datei>`, Endung immer `.jpg`; alle 408 am 27.10.2026
  geprüft), `Bildbeschreibung`, `Tiere` (`true`/`false`), `Tierarten`; fehlende Werte `"NA"`.
- `Geografie` / `Geografie-Pfad`: die geografische Zuordnung des Museums (Thesaurus „MVK Geografie“, wie auf
  der Objektseite), z. B. „Kalawewa“ / „Südasien > Subkontinent > Sri Lanka > Kalawewa“. 405 der 408
  Bilder haben eine; die Genauigkeit schwankt zwischen Ort und Land.
- **`Ortschaft (Route)` ist ein Vorschlag aus String-Abgleich** mit `ortschaften.json` (236 Bilder):
  gleicher Name, ganze Wörter des Routennamens („Hyderabad“ → „Nizamate of Hyderabad“), „heut. …“-Namen
  aus der Notiz („Mumbai“ → „Bombay“), sehr ähnliche Schreibung („Noumea“ → „Nouméa“) und vier feste
  Varianten (Kolkata/Calcutta, Singapore/Singapur, Darjiling/Darjeeling, Jeypore/Jaipur). Hat der genaueste
  Begriff keinen Treffer, zählt der übergeordnete Ort unterhalb der Länderebene („Hanuabada“ → Port Moresby,
  „Negishi“ → Yokohama, „Peradeniya“ → Kandy). Länder und Regionen werden nie einer Station zugeordnet.
- **`Bildbeschreibung`, `Tiere` und `Tierarten` sind KI-generiert** (Claude Sonnet 5.5, 27.10.2026) und
  ungeprüft (`_meta.checked: false`, `_meta.ki`). Tiere sind bewusst großzügig getaggt, auch
  Darstellungen und Tierprodukte (Felle, Federn), gekennzeichnet in Klammern, z. B. „Drache (Darstellung)“.
  `_meta.review` markiert Fälle, in denen das Modell unsicher war.
- `_meta.id`: `ke-image-` + SHA-1 des Dateinamens (10 Zeichen), analog zu den Vault-IDs.
