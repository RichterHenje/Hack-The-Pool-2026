# 19 · Jury Q&A: hard questions and where the answer lives

Written 28 October as a hostile reader of `docs/06_slam.md`, `docs/16_slam_script.md`, and
`docs/18_demo_path.md`. Audiences in the room: Kulturpool and ACDH staff (data providers,
aggregator), museum people (Weltmuseum, KHM, HGM), DH researchers, the other teams. Every answer
points at a file; "fix before slam" marks what the team should change in the talk itself. No
number here that is not in the claims or the script.

### "24 of 70 stations have a Kulturpool record. How do you know those records have anything to do with the voyage?"

We do not claim that. The claim says: a record that names the place and is dated within two years of the voyage. The slam says it the same way. That a hit names the place and not the voyage is a tagged PROPOSED claim in `docs/06_slam.md`, with the Colombo and Columbus example. One record found so far states the voyage itself, an NHM file in `analysis/ke_kulturpool_kontext.md`. Fix before slam: Speaker B says "a dated record that names the place", never "a record of the voyage".

### "You say the museums are not Kulturpool providers, and in the next sentence that the Weltmuseum photographs reached Europeana through Kulturpool. Which is it?"

Both, and that is the finding. The provider facet of the portal, read on 27 October, lists none of the four museums (`docs/02_quests.md`). The Europeana record of the photographs names Kulturpool as provider and the Weltmuseum as data provider, created in 2019 (`docs/06_slam.md`, claim 5). So a delivery exists that the portal does not surface today. We ask Kulturpool why, we do not guess. Fix before slam: keep the two sentences together, as the script has them.

### "How many of the hunting sentences has a person checked against the scans?"

None yet. They are automatic text recognition read by a script, and the talk says so on the slide (`docs/16_slam_script.md`, slide 3). The known false hit is "der Versuchung erlegen", noted in `docs/14_improvements.md`. The check for people is planned as a blind sheet of 20 sentences with scan links; the rubric for machine-proposed links is in `validation/rubric.md`. Fix before slam: if the sheet is filled before 14:00, say the result with its n; if not, say "none yet".

### "Why do you show Weltmuseum photographs at all? Whose rights?"

The Europeana record of these photographs carries CC BY-NC-SA 4.0. The decision of 28 October to show them as images with attribution, and the team's earlier rule of links only, are both in `docs/04_decisions.md`; the attribution line is in `docs/18_demo_path.md`. The slam is non-commercial use with attribution. Fix before slam: the attribution is on screen or spoken whenever an image appears.

### "A hunting trip of the heir to the throne through colonised territories, and you make a map of it. Where is the context?"

The route is the diary's own story; the layers beside it, hunting, killed and collected animals, the people in the photographs, are what reading against the grain means here. The one-sentence context and the pointers to the federal recommendations on collections from colonial contexts and to the CARE principles are in `docs/14_improvements.md`, bucket 2 and 3. The team's decision to add voices as layers, not to rewrite the archive, is in `docs/04_decisions.md`. Fix before slam: Speaker C says the context sentence once, before the demo, and does not celebrate a hunt.

### "70 of 90 stations placed automatically. What about the other 20, and how good are the 70?"

The 20 unplaced stops are small places that GeoNames does not resolve from the vault's spelling; they stay unplaced on purpose, the archive is not corrected (`docs/04_decisions.md`, Tue 11:40). The placed stops carry the GeoNames link and both names where they differ (`prototype/data/ke_itinerary.csv`, recomputed by `scripts/slam_numbers.py`). A gold table with hand coordinates does not exist yet; `docs/08_historic_places.md` lists the open places. Fix before slam: say "placed", not "verified".

### "Which part is yours and which is the team's?"

The day-by-day page with the diary, the hunts, the press, and the photographs is the team's `Kriegsmarine/kaiserin_elisabeth/prototype/reise.html`; the 309 days come from the team's `Kriegsmarine/normalization/json/tagebuch_tage.json`. The station map, the Kulturpool queries per station, the rights check of the photographs, and the claim checker are in this repo (`README.md`, `scripts/slam_numbers.py`). Fix before slam: the slide credits "the KHM team" and the data sources, no individual names.

### "Your diary has 309 days. Yours or theirs, and how do you know the days are right?"

The team's. We compared our own split of the OCR with the team's day list and recommended the team's base (`docs/12_diary_days_quality.md`). Say where the days come from: the 309 days are the day list of franzferdinandsworld.com (14 December 1892 to 18 October 1893); in `tagebuch_tage.json` 107 days rest on a heading printed in the diary, 176 are aligned against that website, and 26 have no entry of their own. The website is an anonymous work in progress that names no edition, so the 176 aligned days are an inference, not a reading of the book. A blind check of 30 printed dates against the scans is prepared in `validation/diary_days_check.csv` and scored by `scripts/diary_days_score.py`, which fails if a control disagrees; the sheet is not filled yet. Fix before slam: if it is filled by 12:00, say the result with its n.

### "Can I reproduce a number you said on stage?"

Every MEASURED number is recomputed from the file its tag names by `scripts/slam_numbers.py`; the tests include a planted wrong number that must fail. Four claims are dated observations that cannot be recomputed offline (an API search, a provider facet, a script run); the checker prints them as PROBE with their date, and `docs/06_slam.md` carries the tag. Fix before slam: run the checker once before 14:00 and say "checked this morning".

### "What does Kulturpool get out of this?"

Three asks in `docs/16_slam_script.md`: which records belong to the voyage, connecting the museums that hold it, and help in checking machine output against the scans. The gap itself is a Data Quality finding: a provider list that does not show a delivery which Europeana shows. The requirements for the submission, licence, public repo, and the pull request into the organisers' examples are in `docs/20_submission.md`.

### "Is the repo public, and under which licence?"

Not yet. The team repo is public; this repo is private until licence and content are checked. The open rows are in `docs/20_submission.md`, the licence discussion in `docs/04_decisions.md`. Fix before slam: the team decides which repo is the result and names the licence on the last slide, or says "to be decided today".

### "Where are the people in the photographs? Do you name them?"

The photographs carry the museum's historical captions, quoted as such; the pop-up wording is in `docs/14_improvements.md`, bucket 1. The CARE principles for depicted people and place names are listed there as the next step, and the recommendation is to talk to the Weltmuseum before any public version. Fix before slam: say "the people in the photographs", not names, unless the museum's caption names them.
