#!/usr/bin/env python3
"""Pressestimmen zur Reise 1892/93 aus ANNO (ÖNB, AustriaN Newspapers Online).

Fragt die Volltextsuche von ANNO ab, die auch die Suchseite
https://anno.onb.ac.at/anno-suche nutzt, Monat für Monat und Begriff für
Begriff. Jeder Treffer bekommt die Etappe der Reiseübersicht
(`../itinerary_1892_93.csv`), die vor dem Erscheinungsdatum zuletzt begann.
Die Ausgabe ist eine Kandidatenliste; was als Pressestimme gilt, entscheidet
ein Mensch am Scan.

Nur Standardbibliothek. Aufruf (aus diesem Ordner):

    python3 anno_search.py                      # alle Begriffe, 1892-12 bis 1893-10
    python3 anno_search.py --months 1893-01:1893-01 --max-docs 20
    python3 -m unittest test_anno_search        # Tests ohne Netz
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://anno.onb.ac.at/anno-suche/rest/search"
HERE = Path(__file__).resolve().parent
PAGE_SIZE = 10  # die API liefert 10 Treffer je Seite, `from` ist der Index des ersten

COLUMNS = [
    # dieselben Spalten wie prototype/data/presse_anno.csv im Prototyp
    "date", "newspaper", "page_url", "place", "quote", "voice", "added_by",
    # Herkunft und Zuordnung
    "query", "doc_id", "page", "hits_in_doc", "itinerary_leg", "days_after_leg_start",
]


class DateFilterIgnored(RuntimeError):
    """Die API hat den Monatsfilter verworfen und liefert Treffer außerhalb."""


# --- Netz -----------------------------------------------------------------

def fetch_json(endpoint: str, params: dict, cache_dir: Path | None, pause: float) -> dict:
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(params)
    cache_file = None
    if cache_dir is not None:
        cache_file = cache_dir / (hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    time.sleep(pause)  # höflich: sequenziell, mit Pause
    if cache_file is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


# --- Suche ------------------------------------------------------------------

def month_range(spec: str) -> list[str]:
    """'1892-12:1893-10' -> ['1892-12', '1893-01', ..., '1893-10']."""
    start, _, end = spec.partition(":")
    end = end or start
    y, m = (int(x) for x in start.split("-"))
    ey, em = (int(x) for x in end.split("-"))
    months = []
    while (y, m) <= (ey, em):
        months.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def check_month(docs: list[dict], month: str) -> None:
    """Abbruch, wenn ein Treffer nicht im angefragten Monat liegt.

    Ein falsch formatiertes Datum (z. B. 18921215) verwirft die API still und
    sucht dann über alle Jahre; das darf nicht als Ergebnis durchgehen.
    """
    for d in docs:
        got = d["uid"]["annoDate"]["date"]
        if not got.startswith(month):
            raise DateFilterIgnored(f"{d['docId']} vom {got} liegt nicht in {month}")


def search_month(query: str, month: str, max_docs: int, fetch) -> tuple[list[dict], int]:
    """Alle Ausgaben eines Monats zu einer Abfrage (höchstens max_docs)."""
    docs: list[dict] = []
    total = 0
    first = 1
    while True:
        data = fetch("complex", {"text": query, "dateFrom": month, "dateTo": month,
                                 "from": first, "facets": "true"})
        total = data.get("totalHits", 0)
        batch = data.get("documents") or []
        check_month(batch, month)
        docs.extend(batch)
        first += PAGE_SIZE
        if not batch or first > total or len(docs) >= max_docs:
            return docs[:max_docs], total


# --- Aufbereitung -------------------------------------------------------------

_TITLE_DATE = re.compile(r"\s+\d{1,2}\.\s+\S+\s+\d{4}$")
_TAG = re.compile(r"<[^>]+>")


def newspaper_name(display_title: str) -> str:
    """'Grazer Volksblatt 17. Dezember 1892' -> 'Grazer Volksblatt'."""
    return _TITLE_DATE.sub("", display_title).strip()


def clean_snippet(text: str) -> str:
    """OCR-Ausschnitt ohne HTML; Silbentrennung am Zeilenende wird zusammengezogen."""
    text = re.sub(r"-\s*<br\s*/?>\s*", "", text)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = html.unescape(_TAG.sub("", text))
    return re.sub(r"\s+", " ", text).strip()


def load_itinerary(path: Path) -> list[dict]:
    legs = []
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if not row["date_from"]:
                continue
            place = row["stay"] or row["to"] or row["from"]
            label = row["stay"] or f"{row['from']} → {row['to']}"
            legs.append({
                "start": date.fromisoformat(row["date_from"]),
                "end": date.fromisoformat(row["date_to"] or row["date_from"]),
                "place": place,
                "label": f"{row['date_from']}–{row['date_to']} {label}",
            })
    return legs


def leg_for(pub: date, legs: list[dict], lag_days: int) -> dict | None:
    """Letzte Etappe, die vor dem Erscheinen begann und höchstens lag_days zurückliegt."""
    best = None
    for leg in legs:
        started = leg["start"] <= pub and (pub - leg["end"]).days <= lag_days
        if started and (best is None or leg["start"] > best["start"]):
            best = leg
    return best


def rows_for_doc(doc: dict, query: str, snippet: dict | None, legs: list[dict],
                 lag_days: int) -> list[dict]:
    pub = date.fromisoformat(doc["uid"]["annoDate"]["date"])
    leg = leg_for(pub, legs, lag_days)
    base = {
        "date": pub.isoformat(),
        "newspaper": newspaper_name(doc.get("displayTitle", "")),
        "place": leg["place"] if leg else "",
        "voice": "",
        "added_by": "",
        "query": query,
        "doc_id": doc["docId"],
        "hits_in_doc": doc.get("totalHitsInDoc", ""),
        "itinerary_leg": leg["label"] if leg else "",
        "days_after_leg_start": (pub - leg["start"]).days if leg else "",
    }
    rows = []
    for page in (snippet or {}).get("snippetPages") or []:
        for s in page.get("snippets") or []:
            # nur die Seiten-URL; imageURL trägt ein kurzlebiges hash-Token
            rows.append({**base, "page": s.get("pageLabel", page.get("pageLabel", "")),
                         "page_url": page.get("openURL", ""), "quote": clean_snippet(s.get("text", ""))})
    if not rows:
        rows.append({**base, "page": "", "page_url": doc.get("openUrl", ""), "quote": ""})
    return rows


def read_terms(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]


# --- Lauf -----------------------------------------------------------------------

def run(args) -> int:
    cache = None if args.no_cache else HERE / "cache"
    def fetch(endpoint, params):
        return fetch_json(endpoint, params, cache, args.pause)

    terms = read_terms(args.terms)
    legs = load_itinerary(args.itinerary)
    seen: dict[str, str] = {}  # doc_id -> erste Abfrage, die es fand
    rows: list[dict] = []
    log = []
    for query in terms:
        for month in month_range(args.months):
            docs, total = search_month(query, month, args.max_docs, fetch)
            new = [d for d in docs if d["docId"] not in seen]
            log.append({"query": query, "month": month, "total_hits": total,
                        "fetched": len(docs), "new_docs": len(new),
                        "capped": total > len(docs)})
            print(f"{month} {query!r}: {total} Ausgaben, {len(docs)} geholt, {len(new)} neu",
                  file=sys.stderr)
            for d in new:
                seen[d["docId"]] = query
                snip = None if args.no_snippets else fetch(
                    "snippet", {"documentId": d["docId"], "query": query})
                rows.extend(rows_for_doc(d, query, snip, legs, args.lag))
    rows.sort(key=lambda r: (r["date"], r["newspaper"], str(r["page"])))
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = {
        "source": API, "months": args.months, "lag_days": args.lag,
        "max_docs_per_month": args.max_docs, "terms": terms,
        "docs": len(seen), "rows": len(rows),
        "rows_without_leg": sum(1 for r in rows if not r["itinerary_leg"]),
        "per_query_month": log,
    }
    args.out.with_name("summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(seen)} Ausgaben, {len(rows)} Zeilen -> {args.out}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--terms", type=Path, default=HERE / "terms.txt")
    p.add_argument("--months", default="1892-12:1893-10", help="JJJJ-MM:JJJJ-MM")
    p.add_argument("--max-docs", type=int, default=200, help="je Begriff und Monat")
    p.add_argument("--lag", type=int, default=21,
                   help="Tage, die eine Meldung nach dem Ende einer Etappe noch zugeordnet wird")
    p.add_argument("--itinerary", type=Path, default=HERE.parent / "itinerary_1892_93.csv")
    p.add_argument("--out", type=Path, default=HERE / "candidates.csv")
    p.add_argument("--pause", type=float, default=1.0)
    p.add_argument("--no-snippets", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
