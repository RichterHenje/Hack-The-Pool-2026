# 10 · Automatische Bereinigung des Vaults (Vorschlag, blind getestet)

Stand 27.10.2026. Ergebnis ist ein **Vorschlag** als eigener Pull Request
(`khm-team-vault-cleanup`) auf eine Kopie des Vaults. Am Vault im Branch `khm-team` wurde
nichts direkt geändert.

## Was der Bereiniger tut (`scripts/vault_clean.py`)

| Regel | was | ändert Text? |
| --- | --- | --- |
| R1 | Eigenschaften (YAML) für jede Notiz: `type`, `id`, `created_by` (`ai-assisted`, wenn die Notiz eine Ranglisten-PDF nennt), `checked: false`, ggf. `review:` | fügt oben einen Block ein |
| R2 | 199x → 189x in Personen-Notizen, **nur** wenn ein Ranglisten-Jahr derselben Notiz höchstens 1 Jahr abweicht; sonst Markierung | ja |
| R2b | Jahr nach 2026 → 1xxx, wenn ein anderes Jahr derselben Zeile höchstens 2 Jahre abweicht („2888“ neben „1889“) | ja |
| R3 | Link ohne Zielnotiz → `[[Titel\|wie geschrieben]]`, nur bei **genau einem** passenden Titel (ohne Groß/Klein, Akzente, Titel wie Dr./Graf/Kapitän, Namensreihenfolge); sonst Markierung | ja |
| R4 | einfache Klammer `[Titel]` (auch `[Dakna Bâgh, (Nepal])]`) → `[[Titel]]`, nur bei genau einem Treffer | ja |
| F1 | mögliche Dubletten in Personen → `review:` | nein |
| F2 | Schiffe/Ereignisse unter Personen, Länder/Regionen unter Ortschaften → `review:` | nein |

Nicht automatisch: Umbenennungen, Rangbezeichnungen, Normdaten, Ortsidentitäten,
Leerzeichen am Zeilenende. Dateien werden als Bytes gelesen und geschrieben (BOM,
Zeilenenden bleiben). Regeln lesen nur den Text unter dem YAML-Block.

## Blindtest (Kontrollen eingefroren vor dem ersten Lauf: `docs/control_battery_vault_cleaner.md`)

Zwei getrennte Hilfs-Agenten haben je eine Vault-Kopie mit **32 bekannten Fehlern** präpariert
(eigener Zufallsstartwert, Positionen nur im Manifest, das nur das Bewertungsskript liest):
6 Jahres-Tippfehler, 2 unmögliche Jahre, 6 Linkvarianten, 3 Links auf erfundene Namen (dürfen
**nicht** umgeschrieben werden), 3 einfache Klammern, 3 Dubletten, 2 Schiffe unter Personen,
2 Fallen (199x ohne Rangliste, darf nicht geändert werden), 5 saubere Notizen (müssen
byte-gleich bleiben).

| | Lauf 1 (Startwert 4711) | Lauf 2 (Startwert 90210) |
| --- | --- | --- |
| eingepflanzte Fehler richtig behandelt | 32 / 32 | 32 / 32 |
| saubere Notizen byte-gleich | 5 / 5 | 5 / 5 |
| jede Regel einmal abgeschaltet → ihre Fehler werden verfehlt (Test kann scheitern) | 6 / 6 | 6 / 6 |
| zweiter Lauf ändert nichts | ja | ja |
| Änderungen außerhalb der Pflanzungen | 15, alle bekannte echte Fehler | 15, dieselben |

**Was die Läufe verändert haben:**
- nach Lauf 1: zwei Fehlalarme in den Markierungen behoben („Ritter, Franz von“ als Dublette
  jedes „Franz“, weil „Ritter“ als Titel galt; Singapur als Land). Dubletten-Markierungen auf
  echten Notizen: 59 → 6 (drei Paare: Cociancig/Gociancig, Hermann/Herrmann, die zwei Mirtl-Seiten);
- nach Lauf 2: Bewertung zeigt jetzt auch unerklärte Änderungen in präparierten Dateien;
- beim echten Lauf: der zweite Durchgang las die eigenen `review:`-Einträge als Text
  (doppelte Markierungen) und Obsidian hätte `[[…]]` in den Eigenschaften als Link gezählt.
  Behoben (Regeln lesen nur den Text, „Link ohne Ziel“ ohne Klammern); beide Läufe danach
  erneut von den unveränderten Kopien: wieder 32 / 32.

**Grenze des Tests:** Die Pflanzungen prüfen die Fehlerarten, für die Regeln geschrieben wurden,
an unbekannten Stellen. Fehlerarten, an die niemand gedacht hat, prüfen sie nicht. Der Vault
war vor dem Test schon gesichtet worden.

## Ergebnis auf dem echten Vault (Stand `4002fd8`)

**Commit 1, Korrekturen (15 in 13 Dateien):** 12 Jahreszahlen 199x → 189x (Havlas, Licen,
Obereigner, Sardoz, Skala 3×, Tusch, Weisgärber, Zeitz, Zelisko, Zodet); Saida 2888 → 1888;
Dakna Bâgh; Kukic. Eyb (1992) nur markiert.

**Commit 2, Eigenschaften für 591 Notizen** (nur Einfügungen), davon 26 mit `review:`:
10 Links ohne Ziel, 6 Dubletten-Hinweise (3 Paare), 15 Typ-Hinweise (13 Länder/Regionen unter
Ortschaften, H.M.S. Zenta und die Weltreise-Notiz unter Personen), 1 Jahreszahl (Eyb).

Commit 2 lässt sich unabhängig von Commit 1 übernehmen oder ablehnen. Nach Änderungen am
Vault neu erzeugen: `uv run python -m scripts.vault_clean <Vault-Ordner> --report <datei.json>`
(ein zweiter Lauf ändert nichts).
