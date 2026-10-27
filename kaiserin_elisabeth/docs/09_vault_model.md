# 09 · Vorschlag: Datenmodell und Informationsarchitektur für den Vault

**Rahmen.** Während des Hackathons wird der Vault nicht bereinigt (Entscheidung in
`04_decisions.md`). Dieses Dokument beschreibt das Modell, das das Team *danach* übernehmen
kann, damit der Bestand für Fachleute nachnutzbar und für die Öffentlichkeit lesbar wird.
Nichts davon ist umgesetzt. Grundlage sind Zählungen vom 27.10.2026 im Branch `khm-team`
(`scripts/vault_review.py`, `analysis/`).

## 1. Befund

| Thema | gemessen | Folge |
| --- | --- | --- |
| Maschinenlesbarkeit | 596 Notizen, **0** mit Eigenschaften (YAML), 4 Tags in Gebrauch (`#Kontakt` 8, `#Route` 7, `#GND`, `#Nordwest-Indien`) | Außer Titeln und Links ist nichts auswertbar; Filter, Tabellen, Exporte gehen nicht |
| Vorlagen | Personen: 383 von 427 nutzen die Vorlage; Firmen 0/36, Sammlungen 0/15, Orte 0/98, Schiffe 3/14 | Die `0_Muster`-Notizen sind Lesehilfen, kein Schema |
| Typen vermischt | in `Personen/`: ein Schiff („H.M.S. Zenta“), ein Ereignis (Weltreise-Notiz), Funktion im Titel („Kapitän Franz Mirtl“); in `Schiffe/`: ein Geschwader; in `Ortschaften/`: 14 von 98 sind Länder oder Regionen; `Sammlungen_Projekte/` mischt Museen, Archive, Vereine und ein Projekt | Der Ordner sagt nicht, was ein Eintrag ist |
| Dubletten | „Kapitän Franz Mirtl“ / „Kommandant Linienschiffs- Kapitän Mirtl“; „Hermann, Hugo“ / „Herrmann, Hugo“ | Unsere Prüfung vergleicht ganze Titel und übersieht Funktionswörter im Titel |
| Information im Titel | „Bombay (Indien, Heut. Mumbai)“ = historischer Name + Land + heutiger Name; „Kaiserin Elisabeth, Kreuzer“ = Name + Typ | Titel tragen Daten, die in Felder gehören; jede Umbenennung bricht Links |
| Ränge | 403 Rolleneinträge in 66 Schreibweisen von etwa 20 Rängen („Seecad.“, „Seecadet“, „Seekad.“) | Nicht zählbar, nicht übersetzbar |
| Daten | Freitext; 13 Tippfehler (1990er statt 1890er, „2888“); zwei Notizen widersprechen sich bei der Weltreise | Keine Zeitleiste, keine Filter |
| Normdaten | GND/VIAF in 2 Notizen, Wikidata in 0 | Keine Verknüpfung mit Bibliotheken, Museen, PFP, Kulturpool |
| Quellen | 275 Seiten nennen den PDF-Dateinamen, 100 einen Hungaricana-Link; KI-Transkription ist nur in der Import-Notiz vermerkt, nicht pro Seite | Herkunft und Prüfstatus einer Angabe sind nicht sichtbar |
| Vernetzung | 10 Links ins Leere, 27 Notizen ohne Links; keine Person verlinkt einen Ort | Das Netz ist schiffszentriert; Personen-Orte-Bezüge fehlen |
| Außerhalb des Repos | Namensliste (1.038 Einträge), Ranglisten-PDFs, Ordner `Archivalien` (Fotosammlung und Sammlerakte Hodek) | Die wichtigsten Primärquellen sind nicht mitversioniert |

## 2. Zielmodell: Typen und Eigenschaften

Obsidian **Properties** und **Bases** sind im Vault bereits aktiviert
(`.obsidian/core-plugins.json`). Das Modell braucht also keine neuen Werkzeuge: jede Notiz
bekommt Eigenschaften, Bases zeigt sie als Tabellen. Die Ordner bleiben; der Typ steht
in der Eigenschaft `type`, nicht im Ordnernamen.

**Typen (Taxonomie)**

| `type` | was | Beispiele heute |
| --- | --- | --- |
| `person` | Mensch | Crew, Offiziere, Fotografen, Sammler, Herrscher |
| `place` | Ort mit Koordinate (Stadt, Hafen, Ankerplatz, Station) | Pola, Colombo, Tsingtau |
| `region` | Land, Region, Meer (ohne Punktkoordinate) | Japan, Ostasien, Mittelmeer, Levante |
| `ship` | einzelnes Schiff | Kaiserin Elisabeth (Kreuzer), Saida (Korvette) |
| `unit` | Verband | k.u.k. Eskader für Ostasien |
| `organisation` | Firma, Dienstleister, Behörde, Verein | Bourne & Shepherd, Indian Government Telegraph |
| `collection` | Bestand in einer Institution | Fotosammlung Hodek, Sammlung Franz Ferdinand |
| `institution` | Museum, Archiv, Bibliothek | Weltmuseum Wien, Kriegsarchiv, Pitt Rivers Museum |
| `event` | Reise, Hafenaufenthalt, Dienstverwendung | Weltreise 1892–93, Hafenaufenthalt Colombo, Verwendung als Seecadet 1895 |
| `source` | Archivale, Listenseite, Foto | Rangliste 1895-11-15 S. 143–144 |
| `work` | Literatur | Höfer 2010, *Imperial Sightseeing* |

**Eigenschaften für alle Typen**

```yaml
id: ke-person-0042          # stabil, nie ändern; der Titel darf sich ändern
type: person
label: "Becker, Alois Ritter von"
aliases: ["Alois von Becker", "Becker, Alois"]     # Schreibvarianten statt Doppelseiten
source: ["[[Rangliste 1892-09-12 S. 12]]"]
created_by: ai-assisted     # human | ai-assisted | import
checked: false              # oder Datum der Prüfung am Original
```

`created_by` und `checked` trennen die Rohtranskription von der Prüfung: die Angabe bleibt,
wie sie gelesen wurde, ihr Status ist sichtbar (Prinzip aus FastCat/SeaLiT, Elicit G0;
im Original noch zu prüfen).

**Zusätzlich je Typ**

```yaml
# person
gnd: ""            # https://d-nb.info/gnd/…
wikidata: ""       # Q…
match_status: none # none | proposed | checked
born: "1842"       # EDTF
died: "1900"
birthplace: "[[Aue bei Schottwien]]"

# place
name_as_written: "Bombay"      # so, wie die Quelle schreibt
name_today: "Mumbai"
geonames: "https://www.geonames.org/1275339/"
wikidata: "Q1156"
lat: 18.975
lon: 72.826
country: IN

# ship
ship_type: "[[Kreuzer]]"
launched: "1890"
fate: "versenkt 1914-11-02, Tsingtau"
wikidata: ""
```

**Ereignisse sind die fehlende Mitte.** Was heute als Aufzählung in Personen- und
Schiffsnotizen steht, wird zu Zeilen:

```yaml
# Dienstverwendung (event)
type: event
event_type: service
person: "[[Accurti, Hugo]]"
ship: "[[Kaiserin Elisabeth, Kreuzer]]"
rank: "[[Seekadett]]"          # Begriff aus der Rangliste unten
rank_as_written: "Seecad."
date: "1895-11-15"            # EDTF; "1895" oder "1895?" wenn unsicher
source: "[[Rangliste 1895-11-15 S. 143–144]]"

# Hafenaufenthalt (event)
type: event
event_type: port_call
ship: "[[Kaiserin Elisabeth, Kreuzer]]"
place: "[[Colombo]]"
arrival: "1893-01-?"
departure: ""
voyage: "[[Weltreise 1892–1893]]"
source: "[[Tagebuch Franz Ferdinand, Bd. 1]]"
```

Die 403 Rolleneinträge und `prototype/data/ke_itinerary.csv` sind genau diese Zeilen; das
Modell gibt ihnen nur einen Ort.

**Kontrollierte Vokabulare** (je eine Notiz pro Begriff, Schreibvarianten als `aliases`):
Ränge (Seekadett, Linienschiffsfähnrich, Linienschiffsleutnant, Fregattenleutnant,
Korvettenkapitän, Fregattenkapitän, Linienschiffskapitän, Schiffsarzt, Maschinenleiter …),
Schiffstypen (Kreuzer, Korvette, Kanonenboot …), Ereignistypen (service, port_call,
voyage, collecting, photograph), Rollen von Organisationen (Fotostudio, Händler, Bahn, Post).

**Daten** in **EDTF** (Library of Congress): `1895-05-15`, `1895`, `1899?`, `1892/1893`,
`189X`. Das erlaubt Unsicherheit ohne Freitext und ist sortierbar.

## 3. Informationsarchitektur

- **Werkbank**: der Obsidian-Vault, wie bisher. Bases-Ansichten: „Crew je Jahr“, „Häfen der
  Weltreise“, „ungeprüfte KI-Seiten“, „Personen ohne Normdaten“, „Orte ohne Koordinate“.
- **Einstiegsnotizen** (Übersichten) je Reise und je Bestand: Weltreise 1892–93, Boxeraufstand
  1900–02, Ostasien 1913–14, Sammlung Franz Ferdinand, Fotosammlung Hodek. Für die
  Öffentlichkeit sind das die Kapitel.
- **Primärquellen ins Repo** oder mit stabilem Link: Namensliste, Ranglisten (Hungaricana-
  Link pro Seite statt Dateiname), `Archivalien`.

## 4. Ausgabe: Exporte statt Handarbeit

| für wen | Format | Standard |
| --- | --- | --- |
| Orte, historische Namen | Linked Places (JSON-LD) | World Historical Gazetteer; liegt als `prototype/data/ke_places.lpf.json` vor |
| Personen | CSV + Wikidata/GND-IDs | Abgleich mit GND (lobid), Wikidata, **PFP des ACDH** (österreichische Personendaten, CIDOC CRM) |
| Objekte, Fotos | EDM | Kulturpool → Europeana |
| alle | CSV + JSON-LD, versioniert | Release mit DOI (Zenodo), Lizenz CC BY 4.0 für Daten, CC0 für reine Metadaten (gängige Wahl, im Team zu entscheiden) |
| Öffentlichkeit | statische Website aus dem Vault (Obsidian Publish oder ein Generator), Karte, Zeitleiste | Rangabkürzungen ausgeschrieben, Quellen sichtbar |

**Regeln**: `CONTRIBUTING.md` mit der Eigenschaftsliste; eine Prüfung bei jedem Push
(`scripts/vault_review.py` als Anfang: fehlende `type`/`id`, Daten außerhalb des Zeitraums,
Links ins Leere, Dubletten über `aliases`).

## 5. Weg dorthin (nach dem Hackathon)

| Schritt | was | Aufwand (geschätzt) |
| --- | --- | --- |
| 1 | Skript ergänzt `type`, `id`, `source`, `created_by`, `checked` aus dem, was schon da ist (Ordner, Import-Notiz, Quellzeilen). Probelauf als Diff, das Team gibt frei | 4–6 h |
| 2 | Information aus Titeln in Eigenschaften (`name_as_written`, `name_today`, `ship_type`); Titel werden Labels; Varianten in `aliases`; Typfehler in Ordnern auflösen | 6–10 h, davon die Hälfte Durchsicht |
| 3 | Ereigniszeilen: Dienstverwendungen aus den 403 Rolleneinträgen, Hafenaufenthalte aus den Routen; Rang-Vokabular | 6–8 h |
| 4 | Normdaten als Vorschläge (`match_status: proposed`), Prüfung an einer Stichprobe mit zwei Personen (Präzision, Kappa) | 4 h + Prüfzeit |
| 5 | Exporte, Website, erstes Release mit DOI | 6–8 h |

Für den Slam taugt daraus ein Satz als Ausblick: „So wird aus dem Archiv eines Teams ein
nachnutzbarer Datensatz“, mit dem Typenschema als Bild. Umgesetzt wird es nicht vor dem Slam.
