"""
Teilt Franz Ferdinands "Tagebuch meiner Reise um die Erde" (OCR, ../Sources/FF Tagebuch Bd. 1/2.md)
in Tage auf.

Problem: Die OCR hat viele Tagesüberschriften im Fließtext verstümmelt ("Sikandarabad -■ Gwali . umi
28, Jännei"); die Markdown-Fassung kennt nur 170 Einträge, das Buch aber rund 284 Tage. Ein Eintrag
umfasst daher oft mehrere Tage.

Vorgehen
- Referenz für die Tage: franzferdinandsworld.com ("Franz Ferdinand's World Tour") führt jeden Tag
  14.12.1892–18.10.1893 mit Ort, 284 davon mit eigener Seite (englische Übersetzung des Tagestextes).
- Die 170 erkannten Überschriften bleiben Anker: ein Eintrag vom Datum D enthält die Tage D bis vor
  den nächsten Eintrag.
- Innerhalb eines Eintrags wird jeder deutsche Satz monoton einem dieser Tage zugeordnet
  (dynamische Programmierung). Punkte gibt es für Gemeinsamkeiten mit dem englischen Tagestext:
  Eigennamen (Anfangsbuchstaben-Präfix), Zahlen, Monats-/Tageszahl verstümmelter Überschriften;
  dazu ein schwacher Lageterm (Textanteil deutsch vs. englisch), der Lücken ohne Treffer füllt.
- Gespeichert werden nur Datum, Ort, OCR-Text und Fundstelle, nicht der Text der Website.

Ausgabe: json/tagebuch_tage.json
Aufruf:  python diary_days.py
"""

import hashlib
import html
import json
import math
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE.parent / "Sources"
CACHE = HERE / ".cache"
OUT = HERE / "json" / "tagebuch_tage.json"
SITE = "http://www.franzferdinandsworld.com/the-journey/"
VOLUMES = {1: "tagebuchmeinerr01ferdgoog", 2: "tagebuchmeinerr00ferdgoog"}
MONTHS_EN = {m: i + 1 for i, m in enumerate("January February March April May June July August September "
                                            "October November December".split())}
MONTHS_DE = {1: r"j[äa]n|jann", 2: r"feb", 3: r"m[äa]r", 4: r"apr|api", 5: r"\bmai\b", 6: r"jun", 7: r"jul",
             8: r"aug", 9: r"sep", 10: r"o[ck]t", 11: r"nov", 12: r"de[cz]|dcc"}
HEADING = re.compile(r"^### (\d{4}-\d{2}-\d{2})(?: · (.*))?$")
SCAN = re.compile(r"\*(?:S\. \S+ · )?Scan (\d+)\*(?: \^scan\d+)?")
LOCATION_W = 3.0   # weight of the position prior (0 = names only)
HEADING_W = 6.0    # bonus for a sentence that looks like the heading of day d


def get(url):
    CACHE.mkdir(exist_ok=True)
    path = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".html")
    if path.exists():
        return path.read_text()
    req = urllib.request.Request(url, headers={"User-Agent": "HackThePool2026-Kriegsmarine/0.1"})
    text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    path.write_text(text)
    time.sleep(0.5)
    return text


def plain(raw):
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    m = re.search(r'<div class="entry-content">(.*)', raw, flags=re.S)
    body = re.split(r"Hinterlasse eine Antwort|Leave a Reply|Links\s*</|<footer", m.group(1) if m else raw)[0]
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def site_days():
    page = re.sub(r"<script.*?</script>|<style.*?</style>", "", get(SITE), flags=re.S)
    days = []
    for blk in re.split(r"<br\s*/?>|</p>|</h\d>|</li>", page):
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", blk))).strip()
        if m := re.search(r"(\d{1,2}) (%s) (189\d)\s*[:;]\s*(.+)$" % "|".join(MONTHS_EN), txt):
            link = re.search(r'href="([^"]+)"', blk)
            url = link.group(1) if link else ""
            days.append({"date": f"{m.group(3)}-{MONTHS_EN[m.group(2)]:02d}-{int(m.group(1)):02d}",
                         "place": m.group(4).strip(), "url": ("http:" + url) if url.startswith("//") else url})
    for d in days:
        d["en"] = plain(get(d["url"])) if d["url"] else ""
    return days


def fold(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def en_names(text):
    """Proper names (capitalised, not sentence-initial) and numbers of an English day text."""
    names = set()
    for sent in re.split(r"(?<=[.!?])\s+", text):
        words = re.findall(r"[A-Za-zÀ-ÿ’'\-]+|\d+", sent)
        for i, w in enumerate(words):
            if w.isdigit() and len(w) >= 2:
                names.add(w)
            elif i > 0 and w[0].isupper() and len(w) >= 4 and w.lower() not in {"the", "this", "that", "these"}:
                names.add(fold(w)[:5])
    return names


def de_tokens(text):
    out = set()
    for w in re.findall(r"[A-Za-zÄÖÜäöüß]+|\d+", text):
        out.add(w if w.isdigit() else fold(w)[:5])
    return out


def read_diary():
    """Entries (heading date, place, band) with their sentences and scan numbers."""
    entries = []
    for band in (1, 2):
        cur, scan = None, None
        for line in (SOURCES / f"FF Tagebuch Bd. {band}.md").read_text().splitlines():
            for m in SCAN.finditer(line):
                scan = int(m.group(1))
            line = SCAN.sub(" ", line).strip()
            if m := HEADING.match(line):
                cur = {"date": m.group(1), "heading": (m.group(2) or "").strip(), "band": band, "sentences": []}
                entries.append(cur)
                continue
            if line.startswith("## ") or cur is None or not line or line.startswith("---"):
                continue
            for s in re.split(r"(?<=[.!?;])\s+", line):
                if s.strip():
                    cur["sentences"].append({"text": s.strip(), "scan": scan})
    return entries


def heading_like(sentence, date):
    """Garbled inline heading '<Ort>, <Tag>. <Monat>' / '<Ort> 27. und 28. Jänner' with the right month;
    the day digits are often broken, so the month decides and a matching day number adds to it."""
    y, m, d = map(int, date.split("-"))
    head = sentence[:90].lower()
    if not re.search(r"(?:,|\b)\s*[\dIlOoSsfi]{1,3}\S{0,2}[.,]?\s*(?:und\s*\S{1,3}[.,]?\s*)?(" + MONTHS_DE[m] + r")\w*",
                     head):
        return 0.0
    return 1.0 if re.search(rf"(?<!\d){d}(?!\d)", head) else 0.6


def align(entry, days, idf):
    """Monotone assignment of an entry's sentences to its candidate days."""
    sents, k = entry["sentences"], len(days)
    if k == 1 or not sents:
        return [0] * len(sents), [0.0] * k
    total_de = sum(len(s["text"]) for s in sents) or 1
    en_len = [max(len(d["en"]), 1) for d in days]
    total_en = sum(en_len)
    centers, acc = [], 0
    for L in en_len:
        centers.append((acc + L / 2) / total_en)
        acc += L
    names = [en_names(d["en"]) for d in days]
    gain = []
    pos = 0
    for s in sents:
        p = (pos + len(s["text"]) / 2) / total_de
        pos += len(s["text"])
        toks = de_tokens(s["text"])
        row = []
        for j, d in enumerate(days):
            g = sum(idf.get(t, 0) for t in toks & names[j])
            g -= LOCATION_W * abs(p - centers[j])
            row.append(g)
        gain.append(row)
    # DP: best[i][j] = best score for sentences 0..i with sentence i on day j (j non-decreasing).
    # Starting day j at sentence i earns a bonus if sentence i looks like day j's heading.
    n = len(sents)
    NEG = -1e18
    enter = [[HEADING_W * heading_like(s["text"], d["date"]) for d in days] for s in sents]
    best = [[NEG] * k for _ in range(n)]
    back = [[0] * k for _ in range(n)]
    best[0][0] = gain[0][0]
    for i in range(1, n):
        run, arg = NEG, 0          # best over days j' < j at sentence i-1
        for j in range(k):
            stay = best[i - 1][j]
            move = run + enter[i][j] if j else NEG
            if stay >= move:
                best[i][j], back[i][j] = stay + gain[i][j], j
            else:
                best[i][j], back[i][j] = move + gain[i][j], arg
            if best[i - 1][j] > run:
                run, arg = best[i - 1][j], j
    j = k - 1   # last sentence belongs to the last day
    path = [0] * n
    for i in range(n - 1, -1, -1):
        path[i] = j
        j = back[i][j]
    # a heading cut by the sentence splitter ("Gwali . | umi 28, Jännei") leaves a short fragment at
    # the end of the previous day: move such fragments to the day they introduce
    for i in range(1, n):
        if path[i] != path[i - 1]:
            m = i
            while m > 0 and path[m - 1] == path[i - 1] and len(sents[m - 1]["text"]) < 60 and i - m < 3:
                m -= 1
            joined = " ".join(s["text"] for s in sents[m:i + 1])
            if m < i and heading_like(joined, days[path[i]]["date"]):
                for x in range(m, i):
                    path[x] = path[i]
    evidence = [0.0] * k
    for i, j in enumerate(path):
        evidence[j] += max(0.0, gain[i][j] + LOCATION_W * 1.0)
    return path, evidence


def main():
    days = site_days()
    paged = [d for d in days if d["url"]]
    df = {}
    for d in paged:
        for t in en_names(d["en"]):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(len(paged) / c) for t, c in df.items()}
    entries = read_diary()
    entry_dates = [e["date"] for e in entries]
    out = []
    for i, e in enumerate(entries):
        nxt = entry_dates[i + 1] if i + 1 < len(entries) else "1893-10-19"
        cand = [d for d in paged if e["date"] <= d["date"] < nxt] or [d for d in days if d["date"] == e["date"]] \
            or [{"date": e["date"], "place": None, "url": "", "en": ""}]
        path, evidence = align(e, cand, idf)
        for j, d in enumerate(cand):
            sents = [s for s, p in zip(e["sentences"], path) if p == j]
            scans = [s["scan"] for s in sents if s["scan"]]
            first = scans[0] if scans else None
            out.append({
                "date": d["date"], "place_site": d["place"], "heading_ocr": e["heading"], "entry_date": e["date"],
                "band": e["band"], "scan": first,
                "page_url": f"https://archive.org/details/{VOLUMES[e['band']]}/page/n{first - 1}/mode/1up" if first else None,
                "site_url": d["url"] or None,
                "method": "heading" if len(cand) == 1 else "aligned",
                "days_in_entry": len(cand),
                "text": " ".join(s["text"] for s in sents),
            })
    # site days without a separate page ("no separate entry") are listed for completeness
    have = {o["date"] for o in out}
    for d in days:
        if d["date"] not in have:
            out.append({"date": d["date"], "place_site": d["place"], "heading_ocr": None, "entry_date": None,
                        "band": None, "scan": None, "page_url": None, "site_url": None,
                        "method": "no_entry", "days_in_entry": 0, "text": ""})
    out.sort(key=lambda o: o["date"])
    OUT.write_text(json.dumps({
        "about": "Tagebuch Franz Ferdinands 1892/93 nach Tagen. text = OCR (unkorrigiert). method: heading = "
                 "Überschrift erkannt, aligned = Tag innerhalb eines Eintrags per Abgleich mit der Tagesliste "
                 "von franzferdinandsworld.com zugeordnet (Eigennamen, Zahlen, verstümmelte Überschriften), "
                 "no_entry = Tag ohne eigenen Eintrag.",
        "source_days": SITE, "days": out}, ensure_ascii=False, indent=1))
    n = {}
    for o in out:
        n[o["method"]] = n.get(o["method"], 0) + 1
    print(f"{len(out)} Tage -> {OUT.relative_to(HERE)}  {n}")


if __name__ == "__main__":
    main()
