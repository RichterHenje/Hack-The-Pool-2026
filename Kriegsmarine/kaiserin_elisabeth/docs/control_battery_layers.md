# Control battery: layers "Sammeln" and "Menschen" (frozen 2026-10-27, before the join script)

What is tested is the **join** (right people and records on the right days), not new rules.
Join script: `scripts/ke_layers.py` (written after this file). Plants by a separate agent in
copies under `htp-blind/layers1/`; manifest read only by the scorer.

## Joins under test

| join | rule |
| --- | --- |
| J1 aboard | person shown on diary day D iff their row is in the **latest crew-list issue dated ≤ D** and its `seit` is ≤ D (empty `seit` counts as ≤ D) |
| J2 local actors | person/company note that links to a vault place note P → shown on the diary days whose heading refers to P; nowhere else |
| J3 collecting sentences | a diary sentence in which the diarist (or his party) acquires, receives, buys, collects or has prepared objects or specimens → listed on that day |
| J4 Kulturpool / Höfer | records attach by date range or to the whole voyage (never by place-string match); Höfer VF numbers only from `hoefer_link/vf_photo_ids.csv` with a named stop |

## Plants (one loop, fresh plants; a second loop only if loop 1 misses)

| class | n | expected |
| --- | ---: | --- |
| A1 crew row with chosen `ausgabe`/`seit` inside the voyage | 4 | on exactly the days the rule gives |
| A2 crew row with `seit` after the voyage end | 2 | on no day |
| L1 invented person linking to a place note whose name appears in diary headings in one spelling | 3 | on exactly the days whose heading contains that name |
| L2 invented person linking to a place note never in the diary | 2 | on no day |
| C1 collecting sentence inserted into a known diary day | 3 | extracted on that day |
| C2 decoy: "Sammlung"/"Museum" in another sense (visit, collection of letters, gathering) | 2 | not extracted |

Pass: every class n of n; with each join disabled its class misses (the scorer can fail);
10 random real days spot-checked by a person against the crew-list page and the vault
(`validation/layers_spotcheck.csv`, yes/no per row). AI-transcribed crew lists are labelled as
such on the page.

## Results (2026-10-27)

Plants written by a separate agent; the manifest was read only by `scripts/ke_layers_score.py`.
Loops in `~/ResearchCode/htp-blind/layers1`, `layers2` (outside the repo).

| class | loop 1 (blind) | loop 2 (blind) | total |
| --- | ---: | ---: | ---: |
| A1 | 4 of 4 | 2 of 2 | 6 of 6 |
| A2 | 2 of 2 | 1 of 1 | 3 of 3 |
| L1 | 3 of 3 | 2 of 2 | 5 of 5 |
| L2 | 2 of 2 | 1 of 1 | 3 of 3 |
| C1 | 1 of 3 | 2 of 5 | **3 of 8** |
| C2 | 2 of 2 | 3 of 3 | 5 of 5 |

Each join disabled: its class drops to 0 in both loops (J1→A1, J2→L1, J3→C1), so the scorer can fail.

Verdict: **J1 (an Bord) and J2 (im Archiv verbunden) PASS. J3 (Sammeln) FAIL** on the pass rule.

What changed between and after the loops:
- After loop 1: acquisition words widened once (missed *erstand*, *erhielt … als Geschenk*).
- After loop 2: two misses were vocabulary (*Messingschalen/Prunkdolch*, *Fächer/Porzellan*), not
  tuned: adding words until the plants pass is the tuned-threshold failure. One miss was a real
  segmentation bug: page-marker lines (`*S. 227 · Scan 240*`) and OCR debris merged into the next
  sentence. Fixed by skipping marker lines, dropping lines that are mostly non-letters (0.8 % of
  diary lines) and splitting sentences per line (one paragraph per line).
  Regression test: `test_layers_page_break_does_not_swallow_next_sentence`.
- Rescored after the fixes (no longer blind, regression only): loop 1 C1 3 of 3, loop 2 C1 3 of 5;
  the two remaining misses are the vocabulary cases above. Score files:
  `validation/layers_loop1_rescore_after_fix.md`, `..._loop2_...` (the blind scores are the table above).

Consequence for the page: "Sammeln und Erwerben" is shown as a labelled search aid, not a count.
Own read of the hits: roughly 4 in 10 sentences are really about acquiring an object (not a
held-out sample, so not a measurement). Real data after the fixes: 170 days, 38 with collecting
sentences, 24 with archive actors, 88 with a place note, 43 medal holders in the crew lists.
A better J3 needs human curation, or an LLM pass run against fresh plants, not more words.

Still open, for people: `validation/layers_spotcheck.csv` (10 random days) and the 20-passage
hunting check against the scans (known false positive: "der Versuchung erlegen", a purchase).
