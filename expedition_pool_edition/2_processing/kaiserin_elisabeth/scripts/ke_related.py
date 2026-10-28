"""Thematic Kulturpool search around the 1892-93 journey (not by ship name).

    uv run python -m scripts.ke_related

Object records rarely name the ship that carried them, so this searches by theme:
the archduke as collector, the 1894 exhibition in the Belvedere, the Schönbrunn zoo,
hunting and taxidermy, the photographers in the vault, ship type and navy life. Each
query runs as an exact phrase, optionally limited to a provider and a date window.
Writes analysis/ke_related_kulturpool.csv (every hit kept: query, provider, title, date,
rights, url) and prints counts. Hits are candidates: a person decides what is related.
"""

from __future__ import annotations

import calendar
import csv
import datetime as dt
from pathlib import Path

from kp import kulturpool as kpa
from kp import rights

OUT = Path("analysis/ke_related_kulturpool.csv")
NHM = "Naturhistorisches Museum Wien"


def ts(year: int) -> int:
    return calendar.timegm(dt.datetime(year, 1, 1).timetuple())


# (theme, phrase, provider or None, (year_from, year_to) or None)
QUERIES = [
    ("Sammler Franz Ferdinand", "Franz Ferdinand", NHM, None),
    ("Sammler Franz Ferdinand", "Erzherzog Franz Ferdinand", None, (1890, 1900)),
    ("Sammler Franz Ferdinand", "Este", NHM, None),
    ("Sammler Franz Ferdinand", "Weltreise", None, (1892, 1900)),
    ("Ausstellung 1894", "Belvedere", None, (1893, 1896)),
    ("Ausstellung 1894", "Sammlungen von der Weltreise", None, None),
    ("Ausstellung 1894", "Konopischt", None, None),
    ("Ausstellung 1894", "Artstetten", None, None),
    ("Tiergarten Schönbrunn", "Tiergarten Schönbrunn", None, (1890, 1900)),
    ("Tiergarten Schönbrunn", "Menagerie", None, (1890, 1900)),
    ("Jagd und Präparation", "Jagdtrophäe", None, None),
    ("Jagd und Präparation", "Präparator", None, (1880, 1910)),
    ("Jagd und Präparation", "Hodek", None, None),
    ("Jagd und Präparation", "Tigerjagd", None, None),
    ("Jagd und Präparation", "Elefantenjagd", None, None),
    ("Fotografen vor Ort", "Deen Dayal", None, None),
    ("Fotografen vor Ort", "Bourne", None, (1880, 1900)),
    ("Fotografen vor Ort", "Skeen", None, None),
    ("Fotografen vor Ort", "Johnston", None, (1880, 1900)),
    ("Schiff und Marine", "Rammkreuzer", None, None),
    ("Schiff und Marine", "Torpedo-Rammkreuzer", None, None),
    ("Schiff und Marine", "Bord-Scenen", None, None),
    ("Schiff und Marine", "Kriegsmarine", None, (1890, 1895)),
    ("Schiff und Marine", "Pola", "Technisches Museum Wien", None),
    ("Orte 1892-93", "Ceylon", None, (1892, 1895)),
    ("Orte 1892-93", "Indien", None, (1892, 1895)),
    ("Orte 1892-93", "Java", None, (1892, 1895)),
    ("Orte 1892-93", "Japan", None, (1892, 1895)),
    ("Orte 1892-93", "Neu-Guinea", None, (1885, 1900)),
]


def main() -> int:
    rows, summary = [], []
    for theme, phrase, provider, years in QUERIES:
        flt = []
        if provider:
            flt.append(f"dataProvider:=`{provider}`")
        if years:
            flt.append(f"dateMin:>={ts(years[0])} && dateMax:<{ts(years[1] + 1)}")
        res = kpa.search(
            f'"{phrase}"',
            per_page=25,
            filter_by=" && ".join(flt) or None,
            facet_by="dataProvider",
            max_facet_values=4,
        )
        provs = "; ".join(f"{c['value']} {c['count']}" for c in res["facet_counts"][0]["counts"])
        summary.append((theme, phrase, provider or "", years, res["found"], provs))
        for d in kpa.docs(res):
            rows.append(
                {
                    "theme": theme,
                    "query": phrase,
                    "filter_provider": provider or "",
                    "filter_years": f"{years[0]}-{years[1]}" if years else "",
                    "provider": d.get("dataProvider", ""),
                    "title": (d.get("title") or "")[:200],
                    "date": ", ".join(d.get("date") or [])[:40],
                    "type": ", ".join(d.get("dcType") or [])[:60],
                    "rights": rights.label(d),
                    "open": rights.is_open(d),
                    "url": d.get("url", ""),
                }
            )
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for theme, phrase, provider, years, found, provs in summary:
        scope = (provider[:12] + " " if provider else "") + (
            f"{years[0]}-{years[1]}" if years else ""
        )
        print(f"{theme:<24} {phrase:<30} {scope:<22} {found:>6}  {provs[:70]}")
    print(f"-> {OUT} ({len(rows)} hits kept, up to 25 per query)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
