# Normalisierung: Weltreise Franz Ferdinands 1892/93

Eingang ist das Team-Material in `../Vault/` und `../Sources/`; beides wird nur gelesen. Ergebnis sind
JSON-Dateien in `json/`, auf denen die Anreicherung (`../enrichment/`) aufsetzt.

```bash
python3 filter_voyage_ff.py  # Vault -> json/weltreise, ortschaften, personen, schiffe, sammlungen_projekte (maßgeblich)
python3 diary_days.py        # Tagebuch (OCR) -> json/tagebuch_tage.json
python3 people_voyage.py     # alle Personen der Reise -> json/personen_reise.json (nach filter_voyage_ff.py)
python3 animal_pictures.py   # Bilder mit Tieren aus json/bilder.json -> json/bilder_tiere.json
```

Nur Python-Standardbibliothek, außer `animal_pictures.py --classify` (Bild-KI, siehe `requirements.txt`).
`diary_days.py` lädt beim ersten Lauf die Tagesliste von franzferdinandsworld.com in `.cache/` (nicht im Repo).

## `filter_voyage_ff.py` (Lisa Gollner) – maßgebliche Auswahl

Filtert aus dem Vault alle Einträge zur Weltreise auf der „Kaiserin Elisabeth“ und schreibt sie in der
Struktur der `0_Muster_*`-Vorlagen; fehlende Werte sind `"NA"`, `_meta` enthält Datei, Vault-`id`
(aus den YAML-Eigenschaften) und den Auswahlgrund. Code und Objektstruktur kommen aus
`filter_voyage.py` (Basis-Modul; direkt aufgerufen schreibt es die ältere Personenauswahl in dieselben
Dateien). Die früheren `*_final.json` heißen seit 27.10.2026 `*.json`; die älteren Fassungen sind in der
Git-Historie.

Personen werden aufgenommen, wenn im Feld „Auszeichnung“ die Seereise-Denkmünze steht oder die Notiz den
Kreuzer „Kaiserin Elisabeth“ verlinkt und an diesem Link kein Jahr oder nur Jahre der Reise (1892/93) stehen.
Die Nennung im Weltreise-Eintrag allein genügt nicht (Oscar Henschel fällt daher heraus).

| Datei | Inhalt (Stand: bereinigter Vault, 27.10.2026) |
| --- | --- |
| `weltreise.json` | die Reise: Beschreibung, Schiff, Besatzung laut Eintrag, Route (Ortsnotizen in Reihenfolge) |
| `ortschaften.json` | 49 Ortsnotizen der Route mit Position(en) auf der Route |
| `personen.json` | 80 Personen (Auswahl wie oben) |
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

Ergänzt `json/personen.json` (80) – mit Code und Objektstruktur aus `filter_voyage.py` – zu 84 Personen
und teilt sie in Gruppen (`_reise.gruppe`):

- **Besatzung** (55): nur mit Beleg – Seereise-Denkmünze, Eintrag in den Ranglisten 15.11.1892–1.9.1893
  (`../Sources/Ranglisten/kaiserin_elisabeth_ranglisten.csv`, Dienstgrade unter `_reise.ranglisten`) oder
  Schiffs-Link mit Reisejahr. Ranglisten-Namen werden der Vault-Notiz zugeordnet (Nachname + erster Vorname,
  Titel und Partikel ignoriert).
- **Begleitung, Wissenschaft, Gastgeber, Diener** laut Tagebuch (kuratierte Liste im Skript): Clam-Martinic,
  Wurmbrand-Stuppach, Kinsky, Prónay; Lorenz von Liburnau, Eduard Hodek jun.; Havelock, Pirie, Stockinger,
  Imhof; Blasius Paskoevič (Diener).
- **Kontakt** (17): übrige Personen aus `personen.json` ohne Besatzungs-Beleg, z. B. der Nizam von Hyderabad,
  Maharadschas, Lala Deen Dayal.
- **ohne Vault-Notiz**: Jagdbegleiter Bedford (Neuguinea).

Nichts wird zusammengeführt. `_reise.vermutlich_dieselbe_wie` markiert Namen, die einer Notiz unter anderer
Schreibweise zugeordnet wurden (Sanchez de la Cerda; Podhorsky → Podhorszky; Erzherzog Leopold Ferdinand) –
und den Tierwärter **„Biaggio“** des Tagebuchs bei **„Paskoevič, Blasius“** (Diener an Bord; Biaggio = Blasius;
1894 nennt die Presse „Biaggio Paste…vich, eines Ragusaners“). `_reise.moegliche_dublette` markiert Notizen mit
fast gleichem Namen (Hermann/Herrmann, Hugo).

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
- `bilder_tiere.json` (`animal_pictures.py`, Lisa Gollner): die 178 Bilder mit Tieren, reduziert auf die
  relevanten Felder, mit `depicted_animals` aus der Bildbeschreibung; optional Bild-KI (CLIP).
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

## `objekte.json`: Objekte der Sammlung Este im Weltmuseum Wien

Wie `bilder.json` außerhalb des Repos aus TMS erzeugt. Auswahl: alle Objekte, die in einem der drei
Inventarbände der Sammlung Este eingetragen sind (`VIO_Este_1`, `VIO_Este_2`,
`VIO_Este_Handschriftliches_Inventar`; in TMS über die gemeinsamen Scans der Inventarseiten), insgesamt
10.082. Enthalten sind nur die **1.798 Objekte, die auf weltmuseumwien.at online sind**.

- Felder: `Inventarnummer`, `Objektbezeichnung`, `Titel`, `Datierung`, `Material`, `Maße`, `Beschreibung`,
  `Abteilung`, `Inventarband`, `Este-Nummer`, `Geografie`, `Geografie-Pfad`, `Ortschaft (Route)`,
  `Karteikarte`, `Weltmuseum-Link`, `Bild-Link` (nur freigegebene Bilder, Hauptbild zuerst),
  `Transkription`; fehlende Werte `"NA"`. Felder wie bei `bilder.json`; `Ortschaft (Route)` ist auch hier ein
  Vorschlag nach denselben Regeln (296 Objekte).
- `Karteikarte` / `Transkription`: die Karteikarten des Museums sind eigene Datensätze, verknüpft mit dem
  Objekt („siehe auch“). Die Transkription der Kartenbilder steht nur dort, wo das **Kartenbild selbst auf
  weltmuseumwien.at freigegeben** ist (1.614 Objekte, 1.961 Kartenseiten); sie gibt dessen Inhalt als Text
  wieder. `bild-link` führt zum Kartenbild. Formatierungsreste (lange Leerzeichen- und Strichfolgen) sind
  gekürzt, der Wortlaut ist unverändert; die Transkriptionen sind nicht geprüft und können Lesefehler enthalten.
- Bild- und Kartenlinks am 27.10.2026 stichprobenartig geprüft (je 40, alle erreichbar).
- `_meta.id`: `ke-object-` + SHA-1 der Inventarnummer (10 Zeichen); `created_by: "tms-export"`.
