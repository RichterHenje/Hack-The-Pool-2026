# SMS Kaiserin Elisabeth 1892–1914 · Prototyp

Das Schiff als Kern: seine Reisen aus dem Vault `../Vault/Archive_Indien_Schiffreisen`, die
Weltreise 1892–93 Tag für Tag aus Franz Ferdinands Tagebuch (`../Sources/`), dazu
Kulturpool-Datensätze, Jagdstellen im Wortlaut und Pressestimmen. Vault und Quellen werden
nur gelesen und nicht verändert.

## Ansehen

Direkt im Browser öffnen (ohne Server, ohne Kartenkacheln):

| Seite | was |
| --- | --- |
| `prototype/reise.html` | **Weltreise 1892–93 Tag für Tag**: Route nach dem Tagebuch, Tageskarten mit Scan-Link, Ebene „Jagd“ (Sätze vom Erlegen/Schießen im Wortlaut), Kulturpool, Presse (ANNO). Direktlink zu einem Tag: `reise.html#1893-01-11` |
| `prototype/index.html` | alle Reisen des Schiffs 1892–1914 aus dem Vault, Kulturpool-Treffer je Station. Direktlink: `index.html#stop=Bombay` |

## Was die Daten zeigen (Stand 27.10.2026)

| | |
| --- | --- |
| Tagebuchtage (15.12.1892–17.10.1893) | 170; 81 auf der Karte, kleine Orte nur in der Tagesliste |
| Tage mit Sätzen vom Erlegen oder Schießen | 65 Tage, 211 Sätze (ungeprüft; genannte Tiere ≠ getötete Tiere) |
| Stationen aller Reisen 1892–1914 (Vault) | 90, davon 70 verortet; 24 mit Kulturpool-Treffern im Zeitfenster |
| Kulturpool-Datensätze, die das Schiff nennen | 2 (Phrasensuche) |
| Vault-Einträge, die im Kulturpool-Text fehlen | 202 von 589 |

**Kontext im Kulturpool** (`analysis/ke_kulturpool_kontext.md`): Intendanzakten des NHM
nennen das Schiff (Z.196/1893: Zoologe Lorenz an Bord, zurückgeschickt) und belegen die
Präparatoren Gebr. Hodek (Jagdtrophäen Kronprinz Rudolfs, Raubvögel); Marine-Weltreisen als
Sammelreisen (Fasana, Saida); Führer durch die Sammlungen von der Weltreise (1894).
Nicht Kulturpool-Partner: KHM, Weltmuseum, HGM, Schönbrunn (Schloss, Tiergarten).

## Mitmachen: Presse aus ANNO

Ausschnitte von Hand in `prototype/data/presse_anno.csv` eintragen
(`date,newspaper,page_url,place,quote,voice,added_by`), dann
`uv run python -m scripts.ke_diary` – die Tageskarten zeigen sie (± 3 Tage).

## Neu erzeugen

Python 3.13, [uv](https://docs.astral.sh/uv/), im Ordner `Kriegsmarine/kaiserin_elisabeth/`:

```
uv run python -m scripts.ke_diary           # Tagebuch -> Tagesroute, Jagdsätze, Presse (reise.html)
uv run python -m scripts.ke_itinerary       # Reisen aus dem Vault -> Stationen, Linien (index.html)
uv run python -m scripts.ke_places_lpf      # historische Ortsnamen (Linked Places)
uv run python -m scripts.ke_stop_records    # Kulturpool-Treffer je Station (index.html)
uv run python -m scripts.ke_related         # thematische Kulturpool-Suche -> analysis/
uv run python -m scripts.ke_arcgis_pack     # Layer für ArcGIS Online
uv run python -m scripts.vault_review       # Auffälligkeiten im Vault
uv run python -m scripts.vault_clean ../Vault/Archive_Indien_Schiffreisen --report data/clean.json   # Bereinigung (ändert Dateien! nur auf einer Kopie/Branch)
uv run --group dev pytest -q
```

Datenstand: Vault `c76376a` (index.html), Tagebuch-Quellen `7ccdfa9` (reise.html).
Das Ortsverzeichnis (GeoNames) wird beim ersten Lauf nach `data/` geladen (nicht im Repo).

## Inhalt

| Pfad | was |
| --- | --- |
| `prototype/` | beide Seiten, Daten, Küstenlinien (Natural Earth), `arcgis/` für ArcGIS Online |
| `kp/` | Kulturpool-API, Ortsverzeichnis (mit Länderbereich je Reiseabschnitt), historische Namen, Rechte |
| `scripts/` | die Schritte oben |
| `analysis/` | Kulturpool-Kontext, Abgleich Vault ↔ Kulturpool, Auffälligkeiten im Vault |
| `docs/08_historic_places.md` | historische Ortsnamen: Linked Places Format, Beleg vs. Gültigkeit |
| `docs/09_vault_model.md` | Vorschlag Datenmodell, Automatisierung vs. Fachleute, Formate (LIDO, EDM, Wikidata, RDF, CIDOC CRM) |
| `docs/10_vault_cleaning.md` | automatische Vault-Bereinigung als Vorschlag (Branch `khm-team-vault-cleanup`): Regeln, zwei Blindtests mit je 32 eingepflanzten Fehlern (32/32), Ergebnis |

## Grenzen

- Tagebuchtext aus der automatischen Texterkennung; Zitate am Scan prüfen.
- „Jagd“ sind Sätze mit erlegen/schießen; „Strecke“ wird nicht gezählt (heißt im Tagebuch meist Entfernung).
- Orte nur aus den Ländern des jeweiligen Reiseabschnitts; kleine Orte bleiben ohne Koordinate.
- Kulturpool-Treffer je Station nennen den Ort in den Jahren der Reise; sie stammen nicht von der Reise.
- Bilder nur bei offenen Rechten; sonst Titel, Lizenz, Link.
- Das Tagebuch ist die Stimme des Erzherzogs. Andere Perspektiven (Begleiter, Mannschaft,
  lokale Akteure, Tiere) kommen als eigene Ebenen dazu, soweit Quellen vorliegen.

## Quellen und Lizenzen

Vault und Quellen des Teams · Franz Ferdinand, *Tagebuch meiner Reise um die Erde* (1895/96,
gemeinfrei, Internet Archive) · Kulturpool API v2 (Rechte je Datensatz) · GeoNames (CC BY 4.0) ·
Wikidata (CC0) · Natural Earth (gemeinfrei) · Leaflet (BSD-2-Clause).

**Lizenz dieses Ordners: vom Team zu entscheiden.**
