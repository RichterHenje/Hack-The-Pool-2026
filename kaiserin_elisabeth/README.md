# SMS Kaiserin Elisabeth 1892–1914 · Prototyp

Die Reisen des Kreuzers SMS Kaiserin Elisabeth aus dem Vault
`Kriegsmarine/Vault/Archive_Indien_Schiffreisen` als Karte: jede Station mit den
Kulturpool-Datensätzen, die den Ort in den Jahren der Reise nennen, und mit den damals
gültigen Ortsnamen. Der Vault wird nur gelesen und nicht verändert.

## Ansehen

`prototype/index.html` im Browser öffnen (funktioniert direkt von der Festplatte, ohne
Server, ohne Kartenkacheln). Direktlink zu einer Station: `index.html#stop=Bombay`.

## Was die Daten zeigen (Stand 27.10.2026)

| | |
| --- | --- |
| Stationen im Vault (Weltreise-Notiz + Schiffsnotiz) | 90, in 6 Abschnitten |
| davon automatisch verortet (GeoNames) | 70 |
| Stationen mit Kulturpool-Treffern im Zeitfenster der Reise (± 2 Jahre) | 24 |
| Kulturpool-Datensätze, die das Schiff mit Namen nennen | 2 |
| Einträge im Vault, die im Kulturpool-Text nicht vorkommen | 202 von 589 |

Treffer nennen den Ort; sie stammen nicht von der Reise („Colombo“ findet auch Kolumbus).
Weltmuseum Wien, KHM, Heeresgeschichtliches Museum und Staatsarchiv liefern nicht an den
Kulturpool.

## Neu erzeugen

Die Daten in `prototype/data/` wurden aus dem Vault-Stand `c76376a` erzeugt. Nach
Änderungen am Vault (Python 3.13, [uv](https://docs.astral.sh/uv/)), im Ordner
`kaiserin_elisabeth/`:

```
uv run python -m scripts.ke_itinerary       # Route aus dem Vault -> ke_itinerary.csv, Stationen, Linien
uv run python -m scripts.ke_places_lpf      # historische Ortsnamen (Linked Places) -> ke_places.lpf.json
uv run python -m scripts.ke_stop_records    # Kulturpool-Treffer je Station + ke_data.js für die Seite
uv run python -m scripts.ke_arcgis_pack     # Layer für ArcGIS Online -> prototype/arcgis/
uv run python -m scripts.vault_review       # Auffälligkeiten im Vault -> analysis/vault_review.md
uv run --group dev pytest -q
```

Das Ortsverzeichnis (GeoNames) wird beim ersten Lauf nach `data/` geladen (nicht im Repo).

## Inhalt

| Pfad | was |
| --- | --- |
| `prototype/` | Kartenseite (Leaflet 1.9.4), Daten, Küstenlinien (Natural Earth) |
| `prototype/arcgis/` | GeoJSON/CSV für ArcGIS Online, mit Zeitfeldern für den Zeitschieber |
| `kp/` | Kulturpool-API, Ortsverzeichnis, historische Namen, Rechteprüfung |
| `scripts/` | die Schritte oben |
| `docs/08_historic_places.md` | historische Ortsnamen: Linked Places Format, Beleg vs. Gültigkeit |
| `docs/09_vault_model.md` | Vorschlag Datenmodell und Informationsarchitektur für den Vault (nach dem Hackathon) |
| `analysis/review_for_team.md` | Auffälligkeiten im Vault (Tippfehler bei Jahreszahlen, Links ins Leere, Dubletten) |

## Grenzen

- Stationen in der Reihenfolge des Vaults, ohne Tagesdaten; Linien verbinden Stationen
  gerade und zeigen keine Seewege.
- 19 kleine Orte ohne Koordinate (zu klein für das Ortsverzeichnis), bewusst nicht ergänzt.
- Bilder nur bei offenen Rechten (alle Rechteangaben OPEN); sonst Titel, Lizenz, Link.

## Quellen und Lizenzen

Vault des Teams (Lizenz offen) · Kulturpool API v2 (Rechte je Datensatz) · GeoNames
(CC BY 4.0) · Wikidata (CC0) · Natural Earth (gemeinfrei) · Leaflet (BSD-2-Clause) ·
Linked Places Format / World Historical Gazetteer Schema v1.2.2.

**Lizenz dieses Ordners: vom Team zu entscheiden.**
