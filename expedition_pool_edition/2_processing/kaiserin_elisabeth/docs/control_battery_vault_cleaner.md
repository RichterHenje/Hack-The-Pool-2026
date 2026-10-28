# Control battery: vault cleaner (frozen 2026-10-27, before the cleaner was written)

**Honest status of step 0.** The real vault was already inspected this morning
(`scripts/vault_review.py`, `analysis/review_for_team.md`), so the rules below are informed by
real output. What is still independent: the cleaner's code does not exist yet, and the
plants are written by a separate agent that the cleaner's author does not see (positions
and values stay in a manifest file read only by the scoring script).

## Rules under test

| rule | does | may change text? |
| --- | --- | --- |
| R1 frontmatter | adds `type`, `id`, `created_by`, `checked` to notes without frontmatter | yes (prepends block) |
| R2 date slip | 199x → 189x in a person note only if a crew-list year of the same note is within ±1 year of 189x; otherwise flag | yes |
| R2b impossible year | a year > 2026 whose 1xxx form is within 2 years of another year on the same line → that 1xxx form | yes |
| R3 broken link | `[[X]]` without a note X: if exactly one note title matches after normalising (case, accents, punctuation, titles and role words, "First Last" ↔ "Last, First"), rewrite to `[[Title\|X]]` (display text kept); else flag | yes / flag |
| R4 single-bracket link | `[X]` (malformed) whose cleaned text matches exactly one note → `[[Title]]` | yes |
| F1 duplicate | titles equal after normalising, or one letter apart with same first name → `review:` entry on both | no (frontmatter only) |
| F2 misfiled | ship or event titles in `Personen`, country/region titles in `Ortschaften` → `review:` entry | no (frontmatter only) |

Not in scope: renames, rank vocabulary, EDTF, authority IDs, place identities, trailing
whitespace (would flood the diff with invisible changes).

## Plants (written by a separate agent, seed per loop, manifest hidden)

| class | n per loop | expected |
| --- | ---: | --- |
| P1 date slip 18xx→19xx in a crew role line that has a list year | 6 | fixed back |
| P2 impossible year (2xxx) on a line with another 18xx year | 2 | fixed back |
| P3 link variant with a unique target (title word, name order, accent dropped) | 6 | `[[Title\|variant]]` |
| P4 link to a name with no note at all | 3 | flagged, **not** rewritten |
| P5 single-bracket link to an existing note | 3 | `[[Title]]` |
| P6 duplicate note under a spelling variant | 3 | `review:` on both notes |
| P7 ship title filed under `Personen` | 2 | `review:` |
| P8 decoy: 199x in free text with no crew-list year nearby | 2 | **unchanged** |
| N  null: new clean notes that already carry complete frontmatter | 5 | byte-identical |

## Pass criteria (per loop)

- every fix class: caught = planted (n of n), correct fix text; P4 and P8: 0 rewrites;
  nulls: 5 of 5 byte-identical;
- every edit outside plants is listed and must map to a real issue in the vault (13 known
  date slips, Saida "2888", Dakna Bâgh, known broken links); unexplained edits = false positives;
- disable-rule check: with each rule switched off, its class scores as missed (the scorer can fail);
- idempotence: a second run on the cleaned copy changes nothing;
- untouched files: SHA-256 equal before/after for every file the cleaner does not report.

Loop 2 uses a fresh seed and fresh plants after the loop-1 rule changes. A control that fires on
the real run stops it until the cause is found.
