# Analysen: Höfer 2010, Reiseübersicht 1892/93 und Tagebuch-Abgleich

Stand 27.10.2026, ca. 12:50. Ergebnisse aus dem Hackathon-Prototyp zur SMS Kaiserin Elisabeth.
Der Vault (`../Vault/`) und die Quellen (`../Sources/`) bleiben unverändert. Diese Dateien sind
eine eigene Schicht daneben. **Alle Verknüpfungen sind Vorschläge aus String-Abgleich**, bis
jemand sie geprüft hat.

## Quelle

Regina Höfer (Hrsg.), *Imperial Sightseeing: Die Indienreise von Erzherzog Franz Ferdinand von
Österreich-Este*, Wien 2010, doi:10.11588/xarep.00001404.
- Die „Reiseübersicht“ (PDF S. 145-151) folgt Franz Ferdinands *Tagebuch meiner Reise um die
  Erde*, 1895, Bd. I Anh. III S. 561-564 und Bd. II Anh. S. 549-563.
- Das Tagebuch selbst liegt in beiden Bänden bei der BHL, doi:10.5962/bhl.title.130758.
- **Hier stehen nur abgeleitete Fakten** (Daten, Orte, Seitenzahlen, Inventarnummern), kein Text und
  keine Bilder aus dem Buch.

## Dateien

| Datei | Inhalt |
| --- | --- |
| `itinerary_1892_93.csv` | Reiseübersicht als Tabelle: 219 datierte Etappen und Aufenthalte, 15.12.1892-18.10.1893, Ortsnamen wie gedruckt, km; Summe 44.775 km |
| `stop_dates.csv` | die 48 Stationen Franz Ferdinands aus dem Prototyp mit erstem und letztem Datum laut Reiseübersicht; 33 eindeutig zugeordnet |
| `vf_photo_ids.csv` | 48 Foto-Inventarnummern des Museums für Völkerkunde (VF_…, heute Weltmuseum Wien), wie bei Höfer gedruckt, mit Seite (erschlossen) |
| `person_links.csv` | Personen-Notizen des Vaults, deren Name bei Höfer vorkommt (19 mit Vor- und Nachname; mindestens 1 Fehltreffer: „Ritter, Franz von“) |
| `day_compare.csv`, `spine_compare.md`, `compare_summary.json` | Tag-für-Tag-Abgleich Reiseübersicht ↔ Tagebuch-Einträge (`Sources/FF Tagebuch`) |
| `itinerary_summary.json` | Zählungen, Abschnitte und die Aufenthalte, die im Prototyp keine Station haben |

## Ergebnisse in Kürze

- **Reiseübersicht und Tagebuch widersprechen sich an keinem der 170 Tagebuchtage.**
  - 143 Tage stimmen schon im String-Abgleich überein.
  - Die 14 Abweichungen sind OCR-Fehler in den Tagebuch-Überschriften („Coloinbo“, „Dehii“,
    „Tukio“) oder andere Namen für dieselbe Seeetappe. Lesung des Agenten, Stichprobe an den
    Scans offen.
- **Höfer füllt Lücken:** 10 der 11 Tagebuchtage ohne Ort bekommen einen. Für die 138 Tage ohne
  Tagebucheintrag gibt es eine datierte Etappe oder einen Aufenthalt.
- **5 Links ohne Zielseite im Vault** sind in der Reiseübersicht datierte Aufenthalte: Siriska,
  Jagdlager am Laroki, Vei Maori (Vault: „Veimauri River“), Redscar Bay, Dakna Bâgh.
- **26 Aufenthalte fehlen als Station.** Die anderen 14 der 40 nicht zugeordneten sind
  Schreibvarianten (Dehli, Jokohama, Tôkio, Buitenzorg …). Neu sind z. B. Kalawewa, Benâres,
  Haidarabad, Katni, Diamond Harbour, Nara, Banff, Narromine.

## Fragen an das Team

1. **Abfahrt:** Höfer und die Reiseübersicht nennen Triest, 15.12.1892. Die Schiffsnotiz im Vault
   nennt Pola, 12.12.1892. Beides kann stimmen (Heimathafen vs. Einschiffung).
2. **„An Bord“:** Die Reiseübersicht folgt Franz Ferdinand, nicht dem Schiff. Für Agra, Delhi,
   Jaipur usw. ist offen, wo das Schiff lag.
3. **Hodek:** Die Weltmuseum-Seiten (z. B. Objekt 503567) verlinken Eduard Hodek jun. (1858-1929)
   auf GND 117525626 („Hodek, Eduard“, Präparator, aktiv 1870). Höfer nennt Hodek jun. selbst
   „Tierpräparator und Fotograf“ (S. 36). Ist der GND-Satz jun. oder sen.?
4. **VF-Nummern:** Die Download-Dateien des Weltmuseums tragen die VF-Nummer im Namen
   (Objekt 503567 → `VF_14814_a.jpg`). Damit ließen sich Höfers 48 Nummern den Weltmuseum-Seiten
   zuordnen. Das Weltmuseum liefert nicht an den Kulturpool.

## Beispiel: 11. Jänner 1893

| Quelle | Angabe |
| --- | --- |
| Weltmuseum Wien, Objekt 503567 | „Sr k.u.k. Hoheit beim erlegten Elephanten“, 11.1.1893, Kalawewa, Eduard Hodek jun., `VF_14814_a.jpg` |
| Tagebuch, Eintrag 11.1.1893 | kein Ort in der Überschrift; Jagdpassagen mit „Elefant“ |
| Höfer, Reiseübersicht | Aufenthalt Kalawewa 7.1.-12.1.1893 |
| Prototyp | Kalawewa ist keine Station |

## Herkunft

Erzeugt mit den Skripten in `analysis/ke_research/hoefer_link/` des Team-Repos
`artxscience-ai/hack-the-pool-2026` (bis zum Slam privat): `hoefer_itinerary.py`,
`hoefer_link.py`, `compare_spine.py`. Der Text des Buchs kam aus Unstructured Transform.
Geprüfte Zeilen wurden im Textlayer des PDFs gegengelesen (vier Datumskorrekturen, Kalawewa,
Summe).
