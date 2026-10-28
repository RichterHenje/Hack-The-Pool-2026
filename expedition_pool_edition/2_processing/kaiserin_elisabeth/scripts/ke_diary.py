"""Franz Ferdinand's diary (1895/96) as the dated route spine, with hunting passages.

    uv run python -m scripts.ke_diary

One record per day of the voyage (309 days, 14.12.1892–18.10.1893), from the diary split into
days by the normalisation (`../normalization/json/tagebuch_tage.json`, diary_days.py). Earlier this
script split the OCR at its 170 `### YYYY-MM-DD · Ort` headings (`1_sources/Sources/FF Tagebuch
Bd. 1.md`, `Bd. 2.md`), but 63 of those entries span several days because the OCR mangled the date
headings in the running text; their hunts and places were dated to the first day of the entry.
The headings are still read, for the place and its coordinates on the days that have one.
Writes ../../3_visualization/web/data/ke_diary.json, .csv and .js:

  per day: date, volume, scan, archive.org page link, heading as printed (days with their own
  heading), kind (stay / transfer / at_sea / unknown), place (from the heading: as printed,
  normalised, coordinates when the gazetteer resolves it; otherwise the place of the day on
  franzferdinandsworld.com, without coordinates; `place_source` says which), entry_date and method
  of the day split, and
  hunting: sentences with a kill verb (erlegte, geschossen, schoss …) quoted verbatim,
  and the animal words that occur IN those sentences.

"Animals named in kill sentences" is not "animals killed": a sentence can name an animal
that was missed, seen or eaten. Counts are candidates until people check them against
the page images (see docs/06_slam.md). The word "Strecke" is NOT used: in this diary it
mostly means distance ("eine Strecke weit in den Canal").
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from kp import geo
from scripts.vault_places import VAULT

SOURCES = VAULT.parents[1] / "Sources"
VOLUMES = {
    "1": ("FF Tagebuch Bd. 1.md", "tagebuchmeinerr01ferdgoog"),
    "2": ("FF Tagebuch Bd. 2.md", "tagebuchmeinerr00ferdgoog"),
}
DAYS = Path("../normalization/json/tagebuch_tage.json")  # the diary by day (normalization/diary_days.py)
OUT = Path("../../3_visualization/web/data")  # the web pages (expedition_pool_edition/3_visualization/web)

KILL = re.compile(
    # not "schoß": in the diary also the noun Schoß ("den jungfräulichen Schoß der Erde")
    r"\b(erlegt\w*|erlegen|erlegte\w*|geschossen|schoss|schossen|"
    r"abgeschossen|niedergestreckt|Doublette|Coup double)\b",
    re.IGNORECASE,
)
# German animal words as printed in the 1890s (stems); matched inside kill sentences only
ANIMALS = {
    "Tiger": r"tiger",
    "Panther/Leopard": r"panther|leopard",
    "Elefant": r"elephant|elefant",
    "Nashorn": r"nashorn|rhinoceros",
    "Bär": r"\bbär",
    "Büffel": r"büffel|bison",
    "Hirsch": r"hirsch|sambur|axis",
    "Antilope/Gazelle": r"antilop|gazelle|nilgau|blackbuck",
    "Wildschwein": r"wildschwein|keiler|\beber|sau\b",
    "Schakal/Hyäne": r"schakal|hyäne",
    "Affe": r"\baffe",
    "Krokodil/Alligator": r"krokodil|alligator|gavial",
    "Känguru": r"känguru|wallaby",
    "Wildvogel": r"\bente|taucher|reiher|flamingo|pelikan|kiebitz|"
    r"uferläufer|schnepfe|pfau|fasan|taube|papagei|kakadu|paradiesvogel|casuar|kasuar|adler|geier|ibis|storch",
    "Fisch/Hai": r"haifisch|\bhai\b|fisch",
}
# Countries per stretch of the journey, from the diary's own sequence of headings. A place
# is only accepted from these countries, so "Livingston" (Montana) cannot become
# Livingstone (Zambia), "Ugi" (Solomon Islands) not Uji (Japan), "Beli" (Nepal) not Bury.
STRETCHES = [
    ("1892-12-15", "1893-01-04", {"EG", "YE", "LK"}),
    ("1893-01-05", "1893-01-17", {"LK"}),
    ("1893-01-18", "1893-03-30", {"IN", "NP"}),
    ("1893-03-31", "1893-04-29", {"SG", "ID", "MY"}),
    ("1893-04-30", "1893-05-27", {"AU"}),
    ("1893-05-28", "1893-07-12", {"NC", "SB", "PG", "ID", "SG", "MY"}),
    ("1893-07-13", "1893-07-29", {"SG", "HK", "CN", "MO"}),
    ("1893-07-30", "1893-08-24", {"JP"}),
    ("1893-08-25", "1893-10-04", {"CA", "US"}),
    ("1893-10-05", "1893-10-18", {"US", "FR", "DE", "AT", "CH"}),
]


def stretch_countries(date: str) -> set[str] | None:
    return next((c for a, b, c in STRETCHES if a <= date <= b), None)


# 1890s German spellings and OCR forms in the diary headings → name the gazetteer knows.
# Spelling help for geocoding only; the page shows the heading as printed.
SPELLINGS = {
    "steamer point": "Aden",
    "coloinbo": "Colombo",
    "kalawewa": "",
    "taiuuir": "Tandur",
    "haidarabad": "Hyderabad",
    "calciitta": "Calcutta",
    "dardschiling": "Darjeeling",
    "darjschiling": "Darjeeling",
    "dehii": "Delhi",
    "dehli": "Delhi",
    "dschodpur": "Jodhpur",
    "dscbodpur": "Jodhpur",
    "h dschodpur": "Jodhpur",
    "dschaipur": "Jaipur",
    "baiavia": "Jakarta",
    "batavia": "Jakarta",
    "buitcnzorg": "Bogor",
    "buitenzorg": "Bogor",
    "tjiandjur": "Cianjur",
    "tandjong priok": "Jakarta",
    "port kennedv": "Port Kennedy",
    "numea": "Nouméa",
    "hongkono": "Hong Kong",
    "hongkong": "Hong Kong",
    "honkong": "Hong Kong",
    "kanton": "Guangzhou",
    "macao": "Macau",
    "kiöto": "Kyoto",
    "kioto": "Kyoto",
    "ki�t�": "Kyoto",
    "tukio": "Tokyo",
    "tokio": "Tokyo",
    "nikko": "Nikko",
    "mijanoschita": "",
    "port said": "Port Said",
    "port saui": "Port Said",
    "amboina": "Ambon",
    "singapur": "Singapore",
    "nagasaki": "Nagasaki",
    "kumamoto": "Kumamoto",
    # Livingston, Montana is under the 15,000 of cities15000; the only US match is Livingston, New Jersey
    "livingston": "",
}


def kind_of(heading: str) -> str:
    h = heading.strip()
    if not h or h in ("–", "-"):
        return "unknown"
    if re.match(r"^in\s*\.?\s*see\b", h, re.IGNORECASE):
        return "at_sea"
    if re.search(r"\s[—–]\s|--+|\s-\s", h):
        return "transfer"
    return "stay"


def location_of(heading: str, kind: str) -> str:
    """The place a day ends at: the last part of a transfer, the stay itself."""
    if kind in ("unknown", "at_sea"):
        return ""
    parts = re.split(r"\s*(?:[—–]|--+|\s-\s)\s*", heading)
    return parts[-1].strip(" .,")


def sentences(text: str) -> list[str]:
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)  # rejoin hyphenated line breaks
    text = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", text) if s.strip()]


def parse_volume(band: str) -> list[dict]:
    md, ident = VOLUMES[band]
    lines = (SOURCES / md).read_text(encoding="utf-8").splitlines()
    entries, cur, scan = [], None, None
    for line in lines:
        m = re.match(r"^\*(?:S\.\s*\S+\s*·\s*)?Scan (\d+)\*", line.strip())
        if m:
            scan = int(m.group(1))
            continue
        h = re.match(r"^### (\d{4}-\d{2}-\d{2})(?:\s*·\s*(.*))?$", line)
        if h:
            cur = {
                "date": h.group(1),
                "heading": (h.group(2) or "").strip(),
                "band": band,
                "scan": scan,
                "ident": ident,
                "text": [],
            }
            entries.append(cur)
        elif cur is not None and not line.startswith("#"):
            cur["text"].append(re.sub(r"\s*\^scan\d+\s*$", "", line))
    return entries


def site_kind(place_site: str) -> tuple[str, str]:
    """Kind and place of a day without its own heading, from the site's place ('Kandy to Kalawewa, Ceylon')."""
    s = re.sub(r"\(.*?\)|\s+–\s+in \d{4}:.*", "", place_site or "").strip()
    if not s or re.search(r"\b(at sea|ocean|red sea|gulf of)\b", s, re.IGNORECASE):
        return ("at_sea" if s else "unknown"), ""
    parts = re.split(r"\s+to\s+|\s+–\s+|\s+—\s+", s.split(";")[-1])
    return ("transfer" if len(parts) > 1 else "stay"), parts[-1].split(",")[0].strip()


def main() -> int:
    gaz = geo.Gazetteer()
    # the OCR headings by date: place and coordinates for the days that have one
    headings = {e["date"]: e for band in VOLUMES for e in parse_volume(band)}
    days = []
    for d in json.loads(DAYS.read_text(encoding="utf-8"))["days"]:
        h = headings.get(d["date"])
        if h:
            heading, k = h["heading"], kind_of(h["heading"])
            loc = location_of(heading, k)
            search = SPELLINGS.get(geo.norm(loc), loc) if loc else ""
            m = gaz.lookup(search, stretch_countries(d["date"])) if search else None
            source = "heading" if loc else ""
        else:
            heading, m = "", None
            k, loc = site_kind(d["place_site"])
            source = "site" if loc else ""
        text = d.get("text") or ""
        kills = [s for s in sentences(text) if KILL.search(s)]
        animals = sorted(
            {a for a, pat in ANIMALS.items() for s in kills if re.search(pat, s, re.IGNORECASE)}
        )
        days.append(
            {
                "date": d["date"],
                "band": int(d["band"]) if d.get("band") else None,
                "scan": d.get("scan"),
                "page_url": d.get("page_url") or "",
                "heading": heading,
                "kind": k,
                "place_as_printed": loc,
                "place_source": source,
                "place": m["name"] if m else "",
                "country": m["country"] if m else "",
                "lat": m["lat"] if m else None,
                "lon": m["lon"] if m else None,
                "geonames": m["geonames"] if m else "",
                "place_site": d["place_site"],
                "ocr_entry": bool(h),  # the OCR has a `### date` heading on this day (170 of the 309 days)
                "entry_date": d["entry_date"],
                "method": d["method"],
                "words": len(text.split()),
                "kill_sentences": len(kills),
                "animals_in_kill_sentences": animals,
                "kill_quotes": [s[:320] for s in kills[:3]],
            }
        )
    days.sort(key=lambda d: d["date"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ke_diary.json").write_text(
        json.dumps(days, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    # Bundle for prototype/reise.html: diary days + hand-curated ANNO clippings (if any)
    presse_csv = OUT / "presse_anno.csv"
    presse = (
        [r for r in csv.DictReader(presse_csv.open(encoding="utf-8-sig")) if r.get("date")]
        if presse_csv.exists()
        else []
    )
    (OUT / "ke_diary.js").write_text(
        "window.KED = " + json.dumps({"days": days, "presse": presse}, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    with (OUT / "ke_diary.csv").open("w", newline="", encoding="utf-8") as fh:
        cols = [c for c in days[0] if c != "kill_quotes"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for d in days:
            w.writerow(
                {**d, "animals_in_kill_sentences": "; ".join(d["animals_in_kill_sentences"])}
            )

    kinds = {}
    for d in days:
        kinds[d["kind"]] = kinds.get(d["kind"], 0) + 1
    located = [d for d in days if d["lat"] is not None]
    hunting = [d for d in days if d["kill_sentences"]]
    print(f"{len(days)} diary days {days[0]['date']}..{days[-1]['date']}; kinds {kinds}")
    print(
        f"located {len(located)} of {sum(1 for d in days if d['place_source'] == 'heading')} days with a heading place"
        f" ({sum(1 for d in days if d['place_source'] == 'site')} more with the site's place, not located)"
    )
    print(
        f"days with kill sentences {len(hunting)}; kill sentences {sum(d['kill_sentences'] for d in days)}"
    )
    unresolved = sorted(
        {d["place_as_printed"] for d in days if d["place_source"] == "heading" and d["lat"] is None}
    )
    print("places not located:", unresolved)
    print(f"-> {OUT}/ke_diary.json, ke_diary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
