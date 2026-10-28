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

## 5. Was sich automatisieren lässt und wo Fachleute nötig sind

Faustregel: automatisieren, wo sich das Ergebnis an der Quelle, an einer Regel oder an einem
Standard prüfen lässt. Fachleute, wo es darum geht, *wer* jemand ist, *was* etwas bedeutet
oder *woher* ein Objekt stammt.

**Voll automatisierbar** (deterministisch, als Diff prüfbar):

| Problem | wie | warum die Qualität hält |
| --- | --- | --- |
| keine Eigenschaften | Skript setzt `type`, `id`, `source`, `created_by`, `checked` aus Ordner und Import-Notiz | mechanisch; das Team gibt den Diff frei |
| Information im Titel | Regeln verschieben sie in Felder (`name_as_written`, `name_today`, `ship_type`) | in `kp/geo.py` mit Tests umgesetzt |
| Daten als Freitext | Umwandlung in EDTF; Jahre außerhalb des Zeitraums markieren | Erkennung sicher; Korrektur bleibt Vorschlag |
| Quelle als PDF-Dateiname (275) | Dateiname + Seite → Hungaricana-Seitenlink | deterministisch; Stichprobe per Auge |
| Links ins Leere (10), Notizen ohne Links (27) | laufende Prüfung (`scripts/vault_review.py`) | reine Liste, kein Urteil |
| Dienstverwendungen und Hafenaufenthalte als Ereignisse | aus den 403 Rolleneinträgen und den Routen | für die Route schon umgesetzt |
| Orte mit eindeutigem heutigem Namen | GeoNames, Wikidata, Mehrdeutigkeit markiert | 70 von 90 verortet |
| Kulturpool-Abdeckung, Exporte, Website, Prüfung bei jedem Push | Skripte, Validatoren | reproduzierbar |

**Automatisch vorschlagen, Mensch prüft Stichprobe:**

| Problem | Maschine | Mensch |
| --- | --- | --- |
| Rang-Schreibweisen (66 → etwa 20) | wendet eine Zuordnungstabelle an | schreibt die Tabelle einmal, prüft seltene Abkürzungen (ca. 30 min) |
| Dubletten (Mirtl, Hermann/Herrmann) | Kandidaten über Varianten und Ähnlichkeit | entscheidet jede Zusammenführung |
| GND/Wikidata/PFP für Offiziere und Prominente | Kandidaten als `proposed` | zwei Personen prüfen eine Stichprobe: Präzision und Übereinstimmung (Vorbild: Bravo Balado et al. 2014, n = 50 je Experiment) |
| KI-transkribierte Crew-Seiten | Konsistenz über die Listen (Laufbahn plausibel, Schreibweise stabil) | Stichprobe gegen die Seitenbilder; erst das ergibt eine Fehlerquote |
| Länder/Regionen unter Orten; gemischte Sammlungen | schlägt `type` vor | bestätigt in einem Durchgang |

**Fachleute nötig** (die Quelle allein entscheidet es nicht):

| Frage | wer |
| --- | --- |
| Bedeutung und Rangfolge von Abkürzungen („L. Sch. L.“, „Mar. Com. Adjct. 2. Cl.“); ob zwei gleichnamige Einträge eine Person sind | Historiker:in der k.u.k. Kriegsmarine |
| widersprüchliche Daten (12.12. vs. 15.12.1892); Tsingtau/Tianjin 1900–02 und 1914; Namensgleichheit mit anderen Schiffen (Torpedodepotschiff 1884) | Marinegeschichte, Originalquellen |
| Archivsignaturen; welches Objekt von welcher Reise stammt (Hodek, Sammlung Franz Ferdinand) | Archiv und Kuratorium (Weltmuseum Wien, Kriegsarchiv) |
| indische Personen, Orte, Firmen (Nizam, Maharajas, Lala Deen Dayal); kolonialer Kontext und Wortwahl; Herkunft ethnographischer Objekte | Südasien-Geschichte, Provenienzforschung, möglichst Kolleg:innen aus den betroffenen Regionen |
| unklare Lesungen in den Ranglisten | Fachleute für die Originale |
| Lizenz für Vault und Fotos, Veröffentlichung personenbezogener Daten | Rechteklärung (Team, Institution) |

KI und Skripte sind verlässlich für Form, Struktur, Konsistenz und Kandidaten, nicht für
Identität, Bedeutung und Provenienz: eine gleichnamige Person, ein gleichnamiges Schiff oder
ein Objekt „aus“ einem Hafen sehen für ein Modell plausibel aus, ob sie stimmen oder nicht
(Wikidata-Suche nach „SMS Saida“ liefert zuerst den Kreuzer von 1912, nicht die Korvette
von 1878). Realistisch: je eine Sitzung mit Marinegeschichte und Kuratorium, je Stichprobe
etwa eine Stunde für zwei Personen.

## 6. Welche Datenstrukturierung: LIDO, Wikidata, EDM, RDF?

Keine Entweder-oder-Frage: das sind Schichten mit verschiedenen Aufgaben.

| | was es ist | für den Vault |
| --- | --- | --- |
| **RDF** | die allgemeine Art, verknüpfte Daten zu schreiben (Subjekt – Prädikat – Objekt); kein Modell. EDM, CIDOC CRM, Linked Places und Wikidata sind in RDF ausgedrückt | als Exportformat (JSON-LD), nicht als Arbeitsformat |
| **EDM** (Europeana Data Model) | Modell für **Objekt-Datensätze** (Foto, Buch, ethnographisches Objekt) mit Beschreibung, Rechten und Digitalisat | **ja, für Objekte.** Der Kulturpool selbst ist EDM (SPARQL-Datenbank und Objekt-API, geprüft am 27.10.2026) und gibt laut Seite „Anbindung an den Kulturpool“ an Europeana in EDM weiter. Welche Formate Institutionen liefern dürfen, steht dort nicht; die Felder der Partner werden auf die des Kulturpools gemappt |
| **LIDO** | XML-Format, mit dem Museen **Objektdaten** aus ihrer Sammlungsdatenbank an Aggregatoren liefern; ereignisorientiert (Herstellung, Sammlung, Nutzung) | **nicht für den Vault.** Relevant, wenn das Weltmuseum oder ein anderes Museum Hodek-Fotos oder Reiseobjekte aus der eigenen Datenbank liefert; das ist dessen System |
| **Wikidata** | gemeinsame Wissensbasis: eine ID je Person, Schiff, Ort, verknüpft mit GND, VIAF, GeoNames, Wikipedia | **ja, als Verknüpfung, nicht als Speicher.** Jede Notiz trägt Wikidata-/GND-IDs; fehlende Schiffe und Offiziere können später als öffentlicher Beitrag angelegt werden. Hauptdaten nicht dort: offen editierbar, kein Platz für Herkunft und Prüfstatus |

**Was in der Liste fehlt, aber am besten passt:**

- **CIDOC CRM**: das Referenzmodell für Personen, Ereignisse und Orte im Kulturerbe, auch
  hinter der PFP des ACDH. Sein Kern ist genau euer Fall: *eine Person diente auf einem
  Schiff in einer Rolle zu einem Datum, laut einer Quelle*. Ihr müsst CIDOC CRM nicht
  selbst schreiben; die Eigenschaften im Vault sind so angelegt (Ereignisse, Abschnitt 2),
  dass ein Export sie übersetzt.
- **Linked Places Format** für Orte mit historischen Namen (liegt vor:
  `prototype/data/ke_places.lpf.json`).
- **EDTF** für Datumsangaben.

**Empfehlung in Schichten:**

| Schicht | Format | warum |
| --- | --- | --- |
| Arbeit (Team) | Obsidian-Eigenschaften (Abschnitt 2): Personen, Schiffe, Orte, Quellen, Ereignisse | für Historiker:innen pflegbar, Tabellen über Bases |
| Identität | Wikidata, GND, GeoNames (mit Status vorgeschlagen/geprüft) | Anschluss an Bibliotheken, Museen, Web, ohne Daten zu kopieren |
| Personen und Ereignisse (Fachwelt) | Export nach CIDOC CRM / RDF (JSON-LD) | Anschluss an PFP und Prosopographie-Projekte |
| Orte | Linked Places Format | World Historical Gazetteer, historische Namen mit Zeitangaben |
| Objekte, Fotos | EDM (oder LIDO, wenn ein Museum liefert) | Weg in Kulturpool und Europeana |
| Öffentlichkeit | CSV + Website, versioniertes Release mit DOI | ohne Vorwissen nutzbar |

Kurz: Personen und Reisen sind **Ereignisse** (CIDOC CRM, Identität über Wikidata/GND);
Fotos und Objekte sind **Objekt-Datensätze** (EDM, bzw. LIDO, wenn ein Museum liefert).
RDF ist die gemeinsame Sprache für den Export.

## 7. Weg dorthin (nach dem Hackathon)

| Schritt | was | Aufwand (geschätzt) |
| --- | --- | --- |
| 1 | Skript ergänzt `type`, `id`, `source`, `created_by`, `checked` aus dem, was schon da ist (Ordner, Import-Notiz, Quellzeilen). Probelauf als Diff, das Team gibt frei | 4–6 h |
| 2 | Information aus Titeln in Eigenschaften (`name_as_written`, `name_today`, `ship_type`); Titel werden Labels; Varianten in `aliases`; Typfehler in Ordnern auflösen | 6–10 h, davon die Hälfte Durchsicht |
| 3 | Ereigniszeilen: Dienstverwendungen aus den 403 Rolleneinträgen, Hafenaufenthalte aus den Routen; Rang-Vokabular | 6–8 h |
| 4 | Normdaten als Vorschläge (`match_status: proposed`), Prüfung an einer Stichprobe mit zwei Personen (Präzision, Kappa) | 4 h + Prüfzeit |
| 5 | Exporte, Website, erstes Release mit DOI | 6–8 h |

Für den Slam taugt daraus ein Satz als Ausblick: „So wird aus dem Archiv eines Teams ein
nachnutzbarer Datensatz“, mit dem Typenschema als Bild. Umgesetzt wird es nicht vor dem Slam.
