"""Step 2: newspaper reception of each hunting episode via the ANNO search API (ÖNB).

API (undocumented REST backend of https://anno.onb.ac.at/anno-suche, see the ÖNB Labs
anno-notebook): /rest/search/complex?text=<lucene>&dateFrom=YYYY-MM-DD&dateTo=...&from=1
returns 10 issues per page; /rest/search/snippet?documentId=..&query=.. returns text
snippets with IIIF crops of the page.

Per episode two queries are run inside a window from the first hunting day to 70 days
after the last (news from India took ~3-6 weeks by mail):
  near  - proximity: "Erzherzog Tiger"~25 OR "Thronfolger Tiger"~25 ...  (precise)
  issue - (Erzherzog OR Thronfolger) AND (<places>) AND (<animals> OR Jagd)  (broad, issue-level)
Issues found by "near" rank first; the top issues get snippets.

Output: data/anno.json
"""
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from common import ROOT, get_json, load, save

API = "https://anno.onb.ac.at/anno-suche/rest/search"
ANIMALS = {a["id"]: a for a in json.loads((ROOT / "animals.json").read_text())}
PLACES = {p["id"]: p for p in json.loads((ROOT / "places.json").read_text())}
PERSON = ["Erzherzog", "Thronfolger"]
HUNT_WORDS = ["Jagd", "Jagden", "erlegt", "erlegte", "Jagdbeute"]
WINDOW_DAYS = 70
PAGES = 3          # 10 issues per page
SNIPPET_DOCS = 12  # issues per episode that get snippets
MIN_KILL_SENTENCES = 4
MIN_BIG_GAME = 2   # non-bird animal mentions in kill sentences
FF = re.compile(r"Erzherzog|Thronfolger|Franz Ferdinand|Ferdinand", re.I)


def term(t):
    """Quote multi-word or hyphenated terms (unquoted hyphens make ANNO return HTTP 400)."""
    return f'"{t}"' if re.search(r"[\s-]", t) else t


def search(text, start, end, pages=PAGES):
    docs, total = [], 0
    for page in range(pages):
        d = get_json(f"{API}/complex", {"text": text, "dateFrom": start, "dateTo": end, "from": 1 + 10 * page})
        total = d.get("totalHits", 0)
        docs += d.get("documents", [])
        if len(docs) >= total:
            break
    return total, docs


def clean_snippet(s):
    s = s.replace('<span class="snp_txt_hl">', "<mark>").replace("</span>", "</mark>")
    s = re.sub(r"<br\s*/?>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s).replace("\u00ad", "")).strip()


def snippets(doc_id, query, keep):
    d = get_json(f"{API}/snippet", {"documentId": doc_id, "query": query})
    out = []
    for p in d.get("snippetPages", []):
        for s in p.get("snippets", []):
            text = clean_snippet(s["text"])
            if keep.search(text):
                out.append({"page": s.get("pageLabel") or s.get("page"), "text": text,
                            "image": s.get("imageURL"), "url": s.get("openURL")})
    return out[:3]


RANK = {"high": 0, "medium": 1, "low": 2, "unchecked": 3}


def relevance(r):
    """high: a snippet names FF/the archduke and matches an episode term; medium: proximity hit."""
    if any(FF.search(s["text"]) and "<mark>" in s["text"] for s in r["snippets"]):
        return "high"
    return "medium" if "near" in r["match"] else "low"


def doc_record(d):
    return {
        "docId": d["docId"], "title": d["displayTitle"], "date": d["uid"].get("annoDate", {}).get("date"),
        "newspaper": d["uid"]["acronym"], "pub_place": ", ".join(d.get("places") or []),
        "url": d["openUrl"], "thumbnail": d.get("thumbnailURL"), "hits_in_issue": d.get("totalHitsInDoc"),
    }


def enrich(h):
    big = [a for a in h["animals"] if a != "bird"][:3] or ["bird"]
    animal_terms = list(dict.fromkeys(t for a in big for t in ANIMALS[a]["anno"]))
    place_terms = list(dict.fromkeys(t for p in h["place_ids"] for t in PLACES[p]["anno"]))
    start = h["start"]
    end = (date.fromisoformat(h["end"]) + timedelta(days=WINDOW_DAYS)).isoformat()
    q_near = " OR ".join(f'"{p} {t}"~25' for p in PERSON for t in animal_terms)
    q_issue = (f"({' OR '.join(PERSON)}) AND ({' OR '.join(map(term, place_terms))}) "
               f"AND ({' OR '.join(animal_terms + HUNT_WORDS)})")
    n_near, near = search(q_near, start, end)
    n_issue, issue = search(q_issue, start, end)

    docs = {}
    for match, found in (("near", near), ("issue", issue)):
        for d in found:
            r = docs.setdefault(d["docId"], doc_record(d) | {"match": []})
            r["match"].append(match)
    ranked = sorted(docs.values(), key=lambda r: ("near" not in r["match"], "issue" not in r["match"],
                                                   -(r["hits_in_issue"] or 0)))
    keep = re.compile("|".join(map(re.escape, animal_terms + ["Jagd", "erlegt"])), re.I)
    snip_query = " OR ".join(map(term, animal_terms + place_terms + ["Jagd", "erlegt"]))  # space = AND
    for r in ranked[:SNIPPET_DOCS]:
        r["snippets"] = snippets(r["docId"], snip_query, keep)
        r["relevance"] = relevance(r)
    ranked.sort(key=lambda r: RANK[r.get("relevance", "unchecked")])
    n_high = sum(r.get("relevance") == "high" for r in ranked)
    print(f"  {h['id']:<32} near={n_near:<4} issue={n_issue:<4} kept={len(ranked):<3} high={n_high}")
    return {
        "hunt_id": h["id"], "window": [start, end],
        "queries": {"near": {"text": q_near, "total": n_near}, "issue": {"text": q_issue, "total": n_issue}},
        "documents": ranked,
    }


def monthly_coverage():
    """Issues per month mentioning FF together with hunting, Dec 1892 - Dec 1893."""
    q = '("Franz Ferdinand" OR Thronfolger) AND (Jagd OR Jagden OR Tiger OR Tigerjagd OR erlegt OR Jagdbeute)'
    q_all = '"Franz Ferdinand" OR Thronfolger'
    months = [(1892, 12)] + [(1893, m) for m in range(1, 13)]
    out = []
    for y, m in months:
        last = (date(y + m // 12, m % 12 + 1, 1) - timedelta(days=1)).isoformat()
        first = f"{y}-{m:02d}-01"
        hunt = get_json(f"{API}/complex", {"text": q, "dateFrom": first, "dateTo": last, "from": 1})["totalHits"]
        allff = get_json(f"{API}/complex", {"text": q_all, "dateFrom": first, "dateTo": last, "from": 1})["totalHits"]
        out.append({"month": f"{y}-{m:02d}", "issues_ff_hunting": hunt, "issues_ff": allff})
    return {"query_hunting": q, "query_all": q_all, "months": out}


TOPICS = [
    {"id": "trophies", "label": "Trophäen und Sammlung nach der Rückkehr",
     "query": '(Erzherzog OR Thronfolger) AND (Tiger OR Elephanten OR Jagdbeute) AND '
              '(Trophäen OR Präparierung OR präpariert OR Sammlung OR Ausstellung)',
     "snippet_query": "Trophäen OR Präparierung OR präpariert OR Tiger OR Elephanten OR Jagdbeute OR Sammlung",
     "keep": r"Trophä|Präpar|Tiger|Elephant|Jagd|Sammlung", "start": "1893-09-01", "end": "1894-12-31"},
    {"id": "diary", "label": "Rezeption des gedruckten Tagebuchs (1895/96)",
     "query": '"Tagebuch meiner Reise um die Erde"',
     "snippet_query": '"Tagebuch meiner Reise um die Erde" OR Jagd OR Tiger',
     "keep": r"Jagd|Tiger|erleg|Reise um die Erde", "start": "1894-06-01", "end": "1898-12-31"},
]


def topic(t):
    total, found = search(t["query"], t["start"], t["end"], pages=5)
    docs = [doc_record(d) for d in found]
    keep = re.compile(t["keep"], re.I)
    for r in docs[:15]:
        r["snippets"] = snippets(r["docId"], t["snippet_query"], keep)
    docs.sort(key=lambda r: not r.get("snippets"))
    print(f"  topic {t['id']:<10} total={total} with snippets={sum(bool(r.get('snippets')) for r in docs)}")
    return {k: t[k] for k in ("id", "label", "query", "start", "end")} | {"total": total, "documents": docs}


def main():
    hunts = [h for h in load("hunts.json") if h["region"] and h["kill_sentences"] >= MIN_KILL_SENTENCES
             and sum(n for a, n in h["animals"].items() if a != "bird") >= MIN_BIG_GAME]
    print(f"ANNO: {len(hunts)} episodes")
    with ThreadPoolExecutor(4) as ex:
        episodes = list(ex.map(enrich, hunts))
    save("anno.json", {
        "source": "ANNO – AustriaN Newspapers Online, Österreichische Nationalbibliothek (metadata CC0)",
        "api": API,
        "episodes": episodes,
        "coverage": monthly_coverage(),
        "topics": [topic(t) for t in TOPICS],
    })


if __name__ == "__main__":
    main()
