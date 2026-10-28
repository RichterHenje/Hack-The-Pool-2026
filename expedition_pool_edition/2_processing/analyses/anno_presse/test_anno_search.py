"""Tests ohne Netz: python3 -m unittest test_anno_search (aus diesem Ordner)."""

import unittest
from datetime import date
from pathlib import Path

import anno_search as a

HERE = Path(__file__).resolve().parent


def doc(doc_id, day, title="Grazer Volksblatt 17. Dezember 1892", hits=3):
    # Form wie in der echten Antwort von /search/complex
    return {"docId": doc_id, "uid": {"acronym": doc_id[5:8], "owner": "ANNO",
                                     "annoDate": {"date": day}},
            "openUrl": f"http://data.onb.ac.at/ANNO/{doc_id[5:]}?ref=anno-search",
            "displayTitle": title, "totalHitsInDoc": hits}


class MonthFilter(unittest.TestCase):
    def test_range_crosses_year(self):
        self.assertEqual(a.month_range("1892-12:1893-02"), ["1892-12", "1893-01", "1893-02"])

    def test_single_month(self):
        self.assertEqual(a.month_range("1893-05"), ["1893-05"])

    def test_ignored_filter_aborts(self):
        # So sieht es aus, wenn die API das Datum verwirft: Treffer aus anderen Jahren
        with self.assertRaises(a.DateFilterIgnored):
            a.check_month([doc("ANNO_gre18921217", "1892-12-17"),
                           doc("ANNO_vll19150329", "1915-03-29")], "1892-12")

    def test_filter_kept_passes(self):
        a.check_month([doc("ANNO_gre18921217", "1892-12-17")], "1892-12")


class Paging(unittest.TestCase):
    def test_pages_until_total_and_caps(self):
        calls = []

        def fetch(endpoint, params):
            calls.append(params["from"])
            start = params["from"]
            n = max(0, min(10, 23 - start + 1))
            return {"totalHits": 23,
                    "documents": [doc(f"ANNO_gre189212{i:02d}", f"1892-12-{i:02d}")
                                  for i in range(start, start + n)]}

        docs, total = a.search_month("q", "1892-12", 200, fetch)
        self.assertEqual((len(docs), total), (23, 23))
        self.assertEqual(calls, [1, 11, 21])
        docs, _ = a.search_month("q", "1892-12", 15, fetch)
        self.assertEqual(len(docs), 15)

    def test_search_aborts_when_filter_ignored(self):
        def fetch(endpoint, params):
            return {"totalHits": 94626, "documents": [doc("ANNO_vll19150329", "1915-03-29")]}

        with self.assertRaises(a.DateFilterIgnored):
            a.search_month("q", "1892-12", 200, fetch)


class Cleaning(unittest.TestCase):
    def test_title_without_date(self):
        self.assertEqual(a.newspaper_name("Grazer Volksblatt 17. Dezember 1892"), "Grazer Volksblatt")
        self.assertEqual(a.newspaper_name("Prager Abendblatt 14. Februar 1893"), "Prager Abendblatt")

    def test_snippet_html_and_hyphenation(self):
        raw = ('...Der Ramm-<br/>kreuzer <span class="snp_txt_hl">.Kaiserin</span> '
               '<span class="snp_txt_hl">Elisabeth\'</span> war von Hunderten<br/>von Booten...')
        self.assertEqual(a.clean_snippet(raw),
                         "...Der Rammkreuzer .Kaiserin Elisabeth' war von Hunderten von Booten...")


LEGS = [
    {"start": date(1892, 12, 15), "end": date(1892, 12, 20), "place": "Port Saïd",
     "label": "1892-12-15–1892-12-20 Triest → Port Saïd"},
    {"start": date(1893, 1, 7), "end": date(1893, 1, 12), "place": "Kalawewa",
     "label": "1893-01-07–1893-01-12 Kalawewa"},
]


class Itinerary(unittest.TestCase):
    def test_latest_started_leg(self):
        self.assertEqual(a.leg_for(date(1893, 1, 20), LEGS, 21)["place"], "Kalawewa")

    def test_latest_wins_when_two_legs_qualify(self):
        # 8.1.1893: Triest-Etappe endete vor 19 Tagen, Kalawewa begann am 7.1.
        self.assertEqual(a.leg_for(date(1893, 1, 8), LEGS, 21)["place"], "Kalawewa")

    def test_before_journey_has_no_leg(self):
        self.assertIsNone(a.leg_for(date(1892, 12, 1), LEGS, 21))

    def test_lag_limits_assignment(self):
        self.assertIsNone(a.leg_for(date(1893, 3, 1), LEGS, 21))
        self.assertEqual(a.leg_for(date(1893, 3, 1), LEGS, 60)["place"], "Kalawewa")

    def test_real_itinerary_file(self):
        legs = a.load_itinerary(HERE.parent / "itinerary_1892_93.csv")
        self.assertGreater(len(legs), 200)
        leg = a.leg_for(date(1892, 12, 17), legs, 21)
        self.assertIn("Triest", leg["label"])


SNIP = {"snippetPages": [{
    "page": 4, "pageLabel": "4",
    "openURL": "http://data.onb.ac.at/ANNO/gre18921217?ref=anno-search&seite=4",
    "snippets": [{"page": 4, "pageLabel": "4", "text": "Ramm-<br/>kreuzer",
                  "imageURL": "https://digital.onb.ac.at/rep/access/x.jpg?hash=abc123"}]}]}


class Rows(unittest.TestCase):
    def test_one_row_per_snippet_without_image_hash(self):
        rows = a.rows_for_doc(doc("ANNO_gre18921217", "1892-12-17"), "q", SNIP, LEGS, 21)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["page"], r["quote"], r["place"]), ("4", "Rammkreuzer", "Port Saïd"))
        self.assertTrue(r["page_url"].endswith("seite=4"))
        self.assertNotIn("hash=", "".join(str(v) for v in r.values()))
        self.assertEqual(set(r), set(a.COLUMNS))

    def test_doc_without_snippets_is_kept(self):
        rows = a.rows_for_doc(doc("ANNO_gre18921217", "1892-12-17"), "q", None, LEGS, 21)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["quote"], "")
        self.assertIn("gre18921217", rows[0]["page_url"])


class Terms(unittest.TestCase):
    def test_shipped_terms_skip_comments(self):
        terms = a.read_terms(HERE / "terms.txt")
        self.assertTrue(terms)
        self.assertFalse(any(t.startswith("#") for t in terms))


if __name__ == "__main__":
    unittest.main()
