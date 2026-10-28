# Microsite · Hack the Pool 2026

Statische Seite zum Hackathon, ohne Build-Schritt. Veröffentlicht über GitHub Pages unter `/site/`.

## Konzept: Die Stadt aus Text

Der Kulturpool wird zur Datenstadt aus *Hackers* (1995). Gläserne Türme tragen Metadaten und echte Objekttitel aus der API. Typografie wirkt wie Licht auf einem Bildschirm.

- **Farben:** Tinte `#06050b` als Raum. Acid-Gelb `#ffe600` für Handlungen, dazu Cyan und Magenta als Licht der Stadt. Jede Quest hat eine eigene Pin-Farbe.
- **Schriften:** *Anybody* für Titel. Die Breitenachse (`wdth`) wird beim Scrollen auf Satzbreite gedehnt. *Doto* als Punktmatrix für Zahlen und Zeiten, *IBM Plex Sans/Mono* für Text und Code.
- **Motive:**
  - Punktmatrix-Wortmarke
  - Quest-Pins
  - 3,5″-Disketten für die Beispiele
  - Retro-Fenster mit Filmausschnitten und Untertiteln in allen Bereichen
  - Inhaltsfenster zum Herumschauen
  - die Innere Stadt als Platine
  - Pool-Licht im Finale
- **Bewegung:** GSAP mit ScrollTrigger, SplitText, ScrambleText und DrawSVG. Wer im System „Bewegung reduzieren“ eingestellt hat, bekommt eine ruhige Seite ohne Dauerschleifen.

## Lokal ansehen

```bash
# im Repo-Wurzelverzeichnis, damit die Links auf ../examples funktionieren
python3 -m http.server 8000
# → http://localhost:8000/site/
```

Testparameter:

| Parameter | Wirkung |
|---|---|
| `?now=2026-10-27T15:00:00%2B01:00` | simuliert die Uhrzeit, für Countdown, Anmeldestatus und die Markierung „jetzt“ im Programm |
| `?motion=off` | ruhiger Modus |
| `?og` | Ansicht fürs Vorschaubild `img/og.jpg` |

## Live-Daten

Alle Abfragen laufen im Browser direkt gegen `api.kulturpool.at` und `sparql.kulturpool.at`, ohne Key:

- **Gesamtzahl, Partnerinstitutionen, Lizenzen, Formate, Objektarten, IIIF, Medientypen, Bildfarben:** eine Facetten-Abfrage auf `/v2/search`
- **Objekte nach Jahrhundert:** zwölf Bereichsfilter auf `dateMin`
- **Ticker:** Facettenzahlen aus derselben Abfrage
- **Stadt-Texturen:** Titel einer Zufallssuche
- **Live-Suche:** `/v2/search` und `/v2/similar?on=image`
- **Status:** Ping auf API und SPARQL

Ist die API nicht erreichbar, zeigt die Seite den Stand vom 6.10.2026.

## Struktur

```
index.html        Inhalt
css/style.css     Gestaltung
js/main.js        Choreografie, Charts, Konsole, Karte, Zeitlogik
js/city.js        WebGL: Flug durch die Datentürme
js/dotmatrix.js   Punktmatrix-Wortmarke
js/caustics.js    WebGL: Licht im Pool (Finale)
js/pool.js        Client für die Kulturpool-API
js/map-data.js    Straßen der Inneren Stadt (aus OpenStreetMap generiert)
media/            Filmausschnitte (MP4, stumm) und Standbilder
fonts/            Schriften (woff2) und OFL-Lizenzen
vendor/gsap/      GSAP 3.15 (inkl. Draggable)
```

## Quellen und Rechte

- **Schriften:** Anybody, Doto, IBM Plex Sans und IBM Plex Mono, SIL Open Font License 1.1 (siehe `fonts/licenses/`)
- **GSAP:** [Standard License](https://gsap.com/standard-license)
- **Karte:** © OpenStreetMap-Mitwirkende, ODbL
- **Filmausschnitte:** *Hackers* (1995, United Artists). Kurze, stumme Ausschnitte als Zitat und Hommage, wie die GIFs in `docs/gifs`. Die Rechte liegen beim Rechteinhaber. Vor einer breiteren Bewerbung bitte prüfen, ob die Nutzung so passt.
