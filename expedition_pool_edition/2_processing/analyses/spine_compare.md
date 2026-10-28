# Diary spine vs Höfer route overview (2026-10-27, 12:39)

Two routes to one source, compared day by day:
- the diary spine (`prototype/data/ke_diary.csv`) reads Franz Ferdinand's diary entries;
- Höfer 2010's route overview (`itinerary_1892_93.csv`) was compiled from the diary's appendices.

`compare_spine.py` → `day_compare.csv`, `compare_summary.json`. The spine was read from the
working copy at 12:38 (sha256 `fb8400f6…`; it had uncommitted changes by another session). Rerun
after its next commit.

## Result

| | n |
| --- | ---: |
| diary days | 170 (15.12.1892–17.10.1893) |
| Höfer rows / days covered | 219 / **308 of 308** (15.12.1892–18.10.1893) |
| diary days without a Höfer row | 0 |
| place agrees (shared name, string match) | **143** |
| place differs (string match) | 14 |
| no place on one side | 13 (diary 11, Höfer 2) |
| kind agrees (at sea / transfer ↔ Höfer leg; stay ↔ Höfer stay) | **150** |
| kind differs | 11 |

**Read by a person (agent), all 14 place differences agree in substance:**
- 11 are OCR noise in the diary headings: Coloinbo, DarJschiling, Dehii, Dscbodpur, Baiavia,
  Svdnev%, MuUengudgery, KeuCaledonien, Burncc, Honkong, Tukio.
- 3 name the same sea leg differently: "In See nach Singapur" ↔ Diamond Harbour → Pulu Besar;
  "In See nach Java" ↔ Singapur → Tandjong-Priok.
- The 11 kind differences are arrival days: the diary heads the day with the place reached, and
  Höfer lists the leg.
- **So the two routes do not contradict each other** on any of the 170 days. This is a proposal
  until a person has checked a sample against the scans (`scan_url` per row).

## What each side adds

- **Höfer → spine:** a place for 10 of the 11 diary days without one, and dated stays between diary
  entries (138 days have no diary entry).
- **Spine → Höfer:** a scan link per day (archive.org) and the hunting passages.
- **Fix made on the way:** the Höfer parser read "bis 5.1." and "27.4. bis 5.5" (no closing dot) as
  single days, which left 16 days uncovered. Fixed; the total row (44,775 km) is now parsed.

## Example: one day, four sources (11 January 1893)

| source | what it says |
| --- | --- |
| Weltmuseum Wien, object 503567 | "Sr k.u.k. Hoheit beim erlegten Elephanten", 11.1.1893, Kalawewa (Sri Lanka), Eduard Hodek jun.; GND link 117525626. **The download file is `VF_14814_a.jpg`** |
| diary spine, 1893-01-11 | kind `unknown`, no place; 10 kill sentences, animal words "Affe; Elefant; Wildvogel"; scan Bd. 1 p. n74 |
| Höfer route overview | stay **Kalawewa 7.1.–12.1.1893** |
| prototype stops | Kalawewa is **not** a stop |

- The photo's date and place fit the diary day and Höfer's stay.
- Höfer gives the diary day its missing place.
- The Weltmuseum's file name gives the VF inventory number.
- VF_14814 is not among the 48 numbers Höfer prints. So the museum's file names are a second
  source of VF numbers, and they could link the 48 Höfer numbers to Weltmuseum pages.
- Caveat: "animals in kill sentences" are candidates, not kills (see `scripts/ke_diary.py`).
