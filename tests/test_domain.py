"""Offline tests — domain logic against recorded feiertage-api.de fixtures.

Run:  pytest tests/test_domain.py -v
"""
import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from feiertage_mcp import domain as dom  # noqa: E402

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_year_ok(self):
        self.assertEqual(dom.validate_year(2026), 2026)
        self.assertEqual(dom.validate_year("2030"), 2030)
        self.assertEqual(dom.validate_year(None), date.today().year)

    def test_year_bad(self):
        for bad in (1899, 2101, "soon", None.__class__ and "x"):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_year(bad)

    def test_state_ok(self):
        self.assertEqual(dom.validate_state("BE"), "BE")
        self.assertEqual(dom.validate_state("be"), "BE")
        self.assertEqual(dom.validate_state("  by "), "BY")
        self.assertEqual(dom.validate_state(None), "NATIONAL")
        self.assertEqual(dom.validate_state("national"), "NATIONAL")

    def test_state_bad(self):
        for bad in ("", "XX", "DE", "Berlin", "B"):
            with self.assertRaises(ValueError, msg=bad):
                dom.validate_state(bad)

    def test_date_ok(self):
        self.assertEqual(dom.validate_date("2026-12-25"),
                         date(2026, 12, 25))
        self.assertEqual(dom.validate_date(" 2026-01-01 "),
                         date(2026, 1, 1))

    def test_date_bad(self):
        for bad in ("", "2026-13-01", "2026-02-30", "25.12.2026",
                    "2026/12/25", "20261225"):
            with self.assertRaises(ValueError, msg=bad):
                dom.validate_date(bad)

    def test_month_ok(self):
        self.assertIsNone(dom.validate_month(None))
        self.assertEqual(dom.validate_month(12), 12)
        self.assertEqual(dom.validate_month("3"), 3)

    def test_month_bad(self):
        for bad in (0, 13, "soon"):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_month(bad)


class TestUrls(unittest.TestCase):
    def test_holidays_url(self):
        self.assertEqual(dom.holidays_url(2026),
                         "https://feiertage-api.de/api/?jahr=2026")
        self.assertEqual(dom.holidays_url(2026, "BE"),
                         "https://feiertage-api.de/api/?jahr=2026&nur_land=BE")
        self.assertEqual(dom.holidays_url(2030, "national"),
                         "https://feiertage-api.de/api/?jahr=2030&nur_land=NATIONAL")

    def test_holidays_url_bad(self):
        with self.assertRaises(ValueError):
            dom.holidays_url(1800)
        with self.assertRaises(ValueError):
            dom.holidays_url(2026, "XX")


class TestParsing(unittest.TestCase):
    def test_parse_national_2026(self):
        rows = dom.parse_holidays(_read("holidays-2026-national.json"))
        self.assertEqual(len(rows), 9)
        first = rows[0]
        self.assertEqual(first["name"], "Neujahrstag")
        self.assertEqual(first["date"], "2026-01-01")
        self.assertEqual(first["weekday"], "Thursday")
        self.assertEqual(first["weekday_de"], "Donnerstag")
        self.assertIsNone(first["note"])
        self.assertFalse(first["note_only"])
        christmas = next(r for r in rows if r["name"] == "1. Weihnachtstag")
        self.assertEqual(christmas["date"], "2026-12-25")
        self.assertEqual(christmas["weekday"], "Friday")
        # sorted by date
        dates = [r["date"] for r in rows]
        self.assertEqual(dates, sorted(dates))

    def test_parse_be_2026(self):
        rows = dom.parse_holidays(_read("holidays-2026-be.json"))
        self.assertEqual(len(rows), 10)
        frauentag = next(r for r in rows if r["name"] == "Frauentag")
        self.assertEqual(frauentag["date"], "2026-03-08")
        self.assertEqual(frauentag["weekday"], "Sunday")
        self.assertEqual(frauentag["weekday_de"], "Sonntag")

    def test_parse_by_2030(self):
        rows = dom.parse_holidays(_read("holidays-2030-by.json"))
        self.assertEqual(len(rows), 15)
        kings = next(r for r in rows
                     if r["name"] == "Heilige Drei Könige")
        self.assertEqual(kings["date"], "2030-01-06")

    def test_parse_invalid_state_null(self):
        with self.assertRaises(ValueError) as cm:
            dom.parse_holidays(_read("holidays-2026-invalid-state.json"))
        self.assertIn("unknown state", str(cm.exception))

    def test_parse_note_only_entry(self):
        text = ('{"Gr\\u00fcndonnerstag": {"datum": null, "hinweis": '
                '"Sch\\u00fcler haben schulfrei."}, '
                '"Karfreitag": {"datum": "2026-04-03", "hinweis": ""}}')
        rows = dom.parse_holidays(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["name"], "Karfreitag")  # dated first
        note = rows[1]
        self.assertEqual(note["name"], "Gründonnerstag")
        self.assertIsNone(note["date"])
        self.assertTrue(note["note_only"])
        self.assertIn("schulfrei", note["note"])
        self.assertNotIn("weekday", note)

    def test_parse_all_states_2026(self):
        all_rows = dom.parse_all_states(_read("holidays-2026-all.json"))
        self.assertEqual(len(all_rows), 17)
        self.assertEqual(len(all_rows["NATIONAL"]), 9)
        self.assertEqual(len(all_rows["BE"]), 10)
        self.assertIn("BW", all_rows)
        self.assertIn("TH", all_rows)

    def test_parse_bad_json(self):
        with self.assertRaises(ValueError):
            dom.parse_holidays("not json {")
        with self.assertRaises(ValueError):
            dom.parse_holidays('["not", "an object"]')
        with self.assertRaises(ValueError):
            dom.parse_all_states('{"BE": "not a dict"}')


class TestHelpers(unittest.TestCase):
    def test_list_states(self):
        states = dom.list_states()
        self.assertEqual(len(states), 17)
        by_code = {s["code"]: s["name"] for s in states}
        self.assertEqual(by_code["BE"], "Berlin")
        self.assertEqual(by_code["BY"], "Bayern")
        self.assertEqual(by_code["NATIONAL"], "Bundesweit (nationwide)")

    def test_holidays_in_month(self):
        rows = dom.parse_holidays(_read("holidays-2026-national.json"))
        dec = dom.holidays_in_month(rows, 12)
        self.assertEqual(len(dec), 2)
        self.assertEqual([r["name"] for r in dec],
                         ["1. Weihnachtstag", "2. Weihnachtstag"])
        self.assertEqual(len(dom.holidays_in_month(rows, None)), 9)
        self.assertEqual(dom.holidays_in_month(rows, 2), [])

    def test_is_holiday(self):
        rows = dom.parse_holidays(_read("holidays-2026-national.json"))
        hit = dom.is_holiday(rows, date(2026, 12, 25))
        self.assertEqual([r["name"] for r in hit], ["1. Weihnachtstag"])
        self.assertEqual(dom.is_holiday(rows, date(2026, 12, 24)), [])

    def test_next_holiday(self):
        rows = dom.parse_holidays(_read("holidays-2026-national.json"))
        nxt = dom.next_holiday(rows, date(2026, 12, 24))
        self.assertEqual(nxt["name"], "1. Weihnachtstag")
        self.assertEqual(nxt["date"], "2026-12-25")
        self.assertEqual(dom.next_holiday(rows, date(2026, 12, 27)), None)
        # on the day itself counts
        self.assertEqual(
            dom.next_holiday(rows, date(2026, 10, 3))["name"],
            "Tag der Deutschen Einheit")

    def test_holidays_between(self):
        rows = dom.parse_holidays(_read("holidays-2026-national.json"))
        out = dom.holidays_between(
            {2026: rows}, date(2026, 12, 20), date(2027, 1, 5))
        self.assertEqual([r["name"] for r in out],
                         ["1. Weihnachtstag", "2. Weihnachtstag"])
        self.assertEqual(
            dom.holidays_between({2026: rows},
                                 date(2026, 6, 1), date(2026, 6, 30)),
            [])
        with self.assertRaises(ValueError):
            dom.holidays_between({2026: rows},
                                 date(2026, 12, 25), date(2026, 12, 24))
        with self.assertRaises(ValueError):
            dom.holidays_between({2026: rows},
                                 date(2026, 1, 1), date(2028, 1, 3))


if __name__ == "__main__":
    unittest.main()
