# Todesursache: Franz Ferdinand

**Team expedition_pool_edition · Hack the Pool 2026**

Die Weltreise des Thronfolgers Franz Ferdinand an Bord S.M.S. Kaiserin Elisabeth 1892/93 und seine Jagden,
als verknüpfter Datensatz aus einem Archiv-Vault, dem gedruckten Tagebuch, Zeitungen (ANNO) und
Museumssammlungen (Kulturpool, Weltmuseum Wien, Europeana).

## Einstieg

**[3_visualization/web/index.html](3_visualization/web/index.html)** ist die Startseite: wie die Daten
entstanden und drei Wege, sie anzusehen. Die Seiten laufen ohne Server; Repository klonen und `index.html`
im Browser öffnen (für die Karten ist eine Internetverbindung nötig).

| Ansicht | Datei |
| --- | --- |
| Startseite | [`3_visualization/web/index.html`](3_visualization/web/index.html) |
| Die Geschichte: Kapitel entlang der 18 Jagden bis Yokohama | [`3_visualization/web/geschichte.html`](3_visualization/web/geschichte.html) |
| Die Reise Tag für Tag auf der Karte von 1872 | [`3_visualization/web/reise.html`](3_visualization/web/reise.html) |
| Die Karte in ArcGIS: offene Ebenen mit Herkunft und Prüfstand je Ebene (Leander Gussmann) | [ArcGIS Online](https://cacgeoportal-hub.maps.arcgis.com/home/item.html?id=977298da4e1a47c380c77a9041e11908#overview), Ebenen und Export in [`3_visualization/arcgis/`](3_visualization/arcgis/) |
| StoryMap „Who was hunted?“: die Reise aus Sicht der Tiere (Leander Gussmann, Englisch) | [arcg.is/0DXKX](https://arcg.is/0DXKX) |

## Aufbau

Der Ordner ist in drei Bereiche geteilt, in der Reihenfolge, in der die Daten fließen:

| Bereich | Inhalt |
| --- | --- |
| [`1_sources/`](1_sources/) | **Importierte Daten**, nur gelesen: [`Vault/`](1_sources/Vault/) (Obsidian-Vault „Archive_Indien_Schiffreisen“ zur k.u.k. Kriegsmarine: Personen, Orte, Schiffe, Sammlungen) und [`Sources/`](1_sources/Sources/) (Tagebuch Franz Ferdinands als OCR, 2 Bände; Ranglisten 1892/93; die PDFs mit Textebene liegen nicht im Repository, sondern bei archive.org: Band 1 ([PDF](https://archive.org/download/tagebuchmeinerr01ferdgoog/tagebuchmeinerr01ferdgoog_text.pdf), 15 MB; [Digitalisat](https://archive.org/details/tagebuchmeinerr01ferdgoog)), Band 2 ([PDF](https://archive.org/download/tagebuchmeinerr00ferdgoog/tagebuchmeinerr00ferdgoog_text.pdf), 56 MB; [Digitalisat](https://archive.org/details/tagebuchmeinerr00ferdgoog))) |
| [`2_processing/`](2_processing/) | **Unsere Arbeit an den Daten**: [`normalization/`](2_processing/normalization/) (Vault und Quellen → JSON, Tagebuch nach Tagen), [`enrichment/`](2_processing/enrichment/) (Wikidata, GeoNames, GND, ANNO, Kulturpool, Europeana, Weltmuseum; Prüfungen), [`analyses/`](2_processing/analyses/) (Höfers Reiseübersicht, Abgleich mit dem Tagebuch, Fotonummern), [`kaiserin_elisabeth/`](2_processing/kaiserin_elisabeth/) (Python-Paket: Vault-Bereinigung, Ortsverzeichnis, Kulturpool-Abgleich, Tests), [`JSON_OVERVIEW.md`](2_processing/JSON_OVERVIEW.md) (alle JSON-Dateien) |
| [`3_visualization/`](3_visualization/) | **Visualisierung**: [`web/`](3_visualization/web/) (die Webseiten mit ihren Daten), [`arcgis/`](3_visualization/arcgis/) (Ebenen und Export der ArcGIS-Karte, Einbettung, Herkunft je Ebene), [`presentation/`](3_visualization/presentation/) (Präsentation, Diagramme zu Datenfluss und Jagdsätzen) |

Datenfluss: `1_sources/` → `2_processing/normalization/` → `2_processing/enrichment/` →
`3_visualization/web/data/` (Schritt 8 der Anreicherung schreibt `ke_enrichment.js`, das die Seiten lesen).
Alle Schritte sind Skripte und lassen sich wiederholen: `2_processing/enrichment/run_all.sh` (API-Antworten
werden zwischengespeichert; für Europeana braucht es `EUROPEANA_API_KEY` in `.env`).

## Team

Rebeka Erdő, Lisa Gollner, Leander Gussmann, Vasyl Holovachko, Simon Mayer, Caroline McKinley, Anna Puhr,
Henje Richter.

## Protokoll

Protokoll vom 27. Oktober 2026 (erster Hackathon-Tag), aus dem Englischen übertragen:

- **Datenmodell:** Welche Metadatenstruktur und welches Schema bauen wir? Hauptentität ist das Schiff
  „Kaiserin Elisabeth“; Reisen gehören als Eigenschaft zum Schiff (Kategorie Schiff → Reise), Personen sind
  eigene Entitäten.
- **Erzählung:** Fokus auf „Kaiserin Elisabeth“ und die Person Franz Ferdinand: seine Abschusslisten?
  Die Kolonie in China? „Die Reise vermenschlichen“. Was davon steht im Obsidian-Vault?
- **Obsidian-Vault:** Datenreduktion – ein Eintrag für die Kaiserin Elisabeth, einer für die Route der Reise.
- **Von außen dazuholen:** Fotos der getöteten Tiere (die Abschusslisten), Zeitungsartikel und öffentliche
  Rezeption.
- **Twist:** nicht nur seine Jagderlebnisse auf einer Karte zeigen, sondern auch seine Dekadenz.
- **Schritte:** 1) Datenbereinigung und Struktur, 2) Anreicherung über die Kulturpool-API (EDM-Schema?),
  3) Oberfläche: Karte der Jagdreise Franz Ferdinands.
- **Aufteilung in drei Gruppen:** 1) Bereinigung und Strukturierung, mit Filtern auf die Reise;
  2) Anreicherung: Zeitungsartikel (ANNO), Tagebuch Franz Ferdinands, Website zur Reise, Tierfotos aus der
  Datenbank des Weltmuseums (von Kurator:innen mit der Reise verknüpft); 3) Oberfläche.

<details>
<summary>Original</summary>

```text
Protokoll 27.10.2026

--> Discussion: Which metadata structure do we want to build?
--> Which meta Schema? 


--> What is our main Entity: The ship "Kaiserin Elisabeth"
--> voyages --> in the category ship --> voyage --> property of ships 
--> persons --> as an entity


--> What is the narrative are we interested in for this Hackathon?
	--> Focusing on "Kaiserin Elisabeth" and the Person "Franz Ferdinand"
	--> using his shooting-lists? Focusing on the Colony in China
	--> "humanizing the trip"
	--> based on this narrative --> what is inside the Obisian Vault?

--> Obsidian Vault: data reduction
	--> entry for Kaiserin Elisabeth 
	--> entry for the route of the voyage
	--> 


--> What do we want to bring in from the outside?
	--> photographs from the killed animals? --> the shooting-lists
	--> newspaper articles/ public reception

--> What Twist could we add?
	--> not only his Hunting experiences on a map --> showing of his decadence 

Steps:
1) data cleaning + structure
2) data Enrichment with the kulturpool API (EDM-Schema?)
3) Interface: map for the Hunting trip of Franz Ferdinand

--> Splitting up into three Groups:
1) data-cleaning/structuring --> based on filters for the voyage 
2) data Enrichment --> newspaper articles (ANNO), Diary of Franz Ferdinand, Website About the Voyage (Adress), Photographs of Animals from 
Weltmuseum Database (connected by curators to the voyage of Franz Ferdinand)
```

</details>

## Entitäten im Vault

Die Liste der Entitäten im Obsidian-Vault, nach Ordnern (Stand 16. Oktober 2026, vor der Bereinigung;
159 Einträge).

<details>
<summary>Liste anzeigen</summary>

**Firmen, Dienstleister, Institutionen** (36)

- A. John & Co, Chemist Druggist + Agra Ice Factory
- Andrew De Silva
- Arnhold, Karberg & Co.
- Badham, Pile & Company- Secunderabad + Bombay- Hosiers &General Outfitters
- Bourne & Shepherd
- Ceylon Parcel Post
- Dr. Ro Ranken and Company
- Eduljee Vookerjee Son
- Frederick Ahrle & Co.
- G. Gaggino & Co.
- Gobindram & Oodeyram
- Goods Traffic Inspectors Office
- H.H. the Nizam Guaranteed State Railway-Hyderabad
- Indian Government Telegraph
- Indian National Post
- Jeypore Museum
- Jodhpore-Bikaner Railway
- Johnston und Hoffmann
- M. E. Maneckji
- M.C. Joonoos & Co – Colombo
- Murray &Co. - Lucknow
- Nazeer Hussein Miniatur Painter
- Nuthoo Ram and Sons
- Paul Möwis
- Peake, Allen & Co –Lucknow
- Peninsular and Oriental Steam Navigation Company
- Pioneer Press - Allahabad
- R. Starcich & Co.
- S. Dragoon
- S. J. Telléry & Co.
- Shik Hosenal
- Simon Arzt
- Thacker & Co. Limited
- The Colombo Apothecaries Co., Limited
- Treacher & Co. Limited- Manufacturing Chemists & General Merchants
- W. L. H. Skeen & Co.

**Ortschaften** (17)

- Agra, (U.P.), Indien
- Alwar, Rajputana (Indien)
- Bombay (Indien, Heut. Mumbai)
- Brit. Ceylon, Heut. Sri Lanka (1815- 1948)
- Calcutta (Indien)
- Colombo (Hauptstadt, Sri Lanka)
- Delhi (Indien)
- Himalaya (Indien)
- Indien, British Raj 1858-1947
- Jaipur (Jeypore), Rajasthan, India
- Jodhpur, Rajasthan, Indien
- Lucknow, (U.P.), Indien
- Nizamate of Hyderabad, State,
- Pola, Istrien
- Rajasthan, India (Rajputana)
- Simla (Indien)
- Uttar Pradesh (Mod. Staat), Indien

**Personen** (79)

- Ahrlé, Frederick
- Becker, Alois Ritter von
- Bém, Jaroslaw, Dr.
- Billitzer, Emmerich Imre
- Bourguignon v. Baumberg, Arthur
- Braganza, Marie Therese von
- Bugel, Edmund
- Bussatto, Luigi
- Cerda, Anton Sanchez de la
- Clam-Martinic, Heinrich Graf
- Daublebsky Freiherr von Sterneck, Maximilian
- Dayal, Lala Deen
- Dr. Krausz
- Erzherzog Franz Ferdinand  von Österreich-Este
- Gamisch, Anton
- Gianone, Coloman
- Gratzl, August
- Gründorf von Zebegényi, Hans Ritter
- Havelock, Arthur E.
- Hermann, Hugo
- Hodek, Eduard
- Imhof, Max von
- Janaczek, Franz
- Jeitler, Franz
- Kammermaier, Josef
- Kerr, Charles
- Kinsky zu Wichnitz und Tettau, Karl Graf
- Koch, Ernst
- Kopetzky, Josef
- Kukic, Alexander
- Kuralt, Johann
- Lanjus von Wellenberg, Karl Franz Graf
- Laube, Guido
- Libra, Ludwig
- Licen, Johann
- Ludwig Ritter von Höhnel
- Maharaja Jai Singh, Rajput Alwar
- Maharaja Sir Pratap Singh
- Mahmud
- Mallinarich v. Silbergrund, Eugen
- Man, Edward Horace
- Metzger, Otto Edl. v.
- Milić, Alois
- Modes, Lukas
- Mr. Murray
- Nizam von Hyderabad
- Nobl, Dr. Adolf
- Paskoevič, Blasius
- Pauley (Panky), Dr.
- Perkon, Anton
- Pirie, Captain
- Plowden, Trevor C.
- Plumert, Arthur, Dr.
- Pozzi, Sigismund Ritt. v.
- Preuschen v.u.z. Liebenstein, Ernst
- Prónay von Tót-Próna und Blatnicza, Julius
- Pucher, Thomas
- Rada, Raimund
- Raja Sir Sourindro Mohun Tagore
- Ramberg, August Freiherr von
- Reiter, Michael
- Reményi, Franz
- Ritter von Jedina, Hermann
- Ritter von Liburnau, Dr. Ludwig Lorenz
- Salvator von Österreich-Toskana, Erzherzog Leopold Ferdinand
- Skala, Karl
- Sommer, Hubert
- Sore, Michael
- Stejskal, Vaclav
- Stockinger, Franz
- Svoboda, Dr. Vaclav (Wenzel)
- Switak, Karl
- Turina, August
- Valenta, Ludwig
- Wolf, Dr. Anton
- Wünschek, Alfons
- Wurmbrand-Stuppach, Leo Graf
- Zrzavecky, Josef
- Zutphen, Bernardus van

**Sammlungen und Projekte** (15)

- British Museum, London
- Das Historische und Schifffahrtsmuseum Istriens
- Erzherzog Franz Ferdinand Museum im Schloß Artstetten
- Global Sea Routes (GSR)
- Heeresgeschichtliches Museum
- Lloyd, Italien Liners - Historical Society (Triest)
- Museo del Mare, Porto Vecchio Trieste
- Museum für Völkerkunde, Leipzig
- Nachlass-Sammlung der Österreichischen Zentralbibliothek für Physik und Fachbibliothek Chemie
- Naprstek Museum, Prag
- Naturhistorisches Museum
- Pitt Rivers Museum, Oxford
- Rijksmuseum voor Volkenkunde in Leiden
- Staatsarchiv - Kriegsarchiv
- Verein k.u.k. Kriegsmarine Archiv

**Schiffe** (12)

- Albatros, Kanonenboot
- Aspern, Kreuzer
- Aurora, Korvette
- Fasana, Korvette
- Frundsberg, Korvette
- Kaiser Karl VI., Kreuzer
- Kaiserin Elisabeth, Kreuzer
- Leopard, Kreuzer
- Nautilus, Kanonenbot
- Panther, Kreuzer
- Saida, Corvette
- Zrinyi, Korvette

</details>
