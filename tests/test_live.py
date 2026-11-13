"""Live tests — hit the real feiertage-api.de API. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set FEIERTAGE_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from feiertage_mcp import server as srv  # noqa: E402

pytestmark = pytest.mark.live
SKIP = os.environ.get("FEIERTAGE_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="FEIERTAGE_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_list_holidays_live(self):
        out = json.loads(srv.feiertage_list_holidays(2026, "NATIONAL"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 9)
        names = [h["name"] for h in out["holidays"]]
        self.assertIn("Tag der Deutschen Einheit", names)
        unity = next(h for h in out["holidays"]
                     if h["name"] == "Tag der Deutschen Einheit")
        self.assertEqual(unity["date"], "2026-10-03")
        self.assertEqual(unity["weekday"], "Saturday")
        print("\nLIVE 2026 NATIONAL: 9 holidays")

    def test_list_holidays_month_live(self):
        out = json.loads(srv.feiertage_list_holidays(2026, "BE", month=3))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["holidays"][0]["name"], "Frauentag")
        self.assertEqual(out["holidays"][0]["date"], "2026-03-08")
        print("\nLIVE 2026 BE March: Frauentag only")

    def test_is_holiday_live(self):
        out = json.loads(srv.feiertage_is_holiday("2026-12-25"))
        self.assertNotIn("error", out)
        self.assertTrue(out["is_holiday"])
        self.assertEqual(out["holidays"], ["1. Weihnachtstag"])
        self.assertEqual(out["weekday"], "Friday")
        out2 = json.loads(srv.feiertage_is_holiday("2026-12-24"))
        self.assertFalse(out2["is_holiday"])
        self.assertEqual(out2["holidays"], [])
        print("\nLIVE is_holiday: 2026-12-25 yes, 2026-12-24 no")

    def test_next_holiday_live(self):
        out = json.loads(srv.feiertage_next_holiday("2026-12-24"))
        self.assertNotIn("error", out)
        self.assertEqual(out["next_holiday"]["name"], "1. Weihnachtstag")
        self.assertEqual(out["next_holiday"]["date"], "2026-12-25")
        # year boundary: nothing left in 2026 after 27 Dec
        out2 = json.loads(srv.feiertage_next_holiday("2026-12-27"))
        self.assertEqual(out2["next_holiday"]["name"], "Neujahrstag")
        self.assertEqual(out2["next_holiday"]["date"], "2027-01-01")
        print("\nLIVE next_holiday: 2026-12-24 -> 25 Dec; 2026-12-27 -> 2027-01-01")

    def test_holidays_between_live(self):
        out = json.loads(srv.feiertage_holidays_between(
            "2026-12-24", "2027-01-02"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 3)
        self.assertEqual([h["name"] for h in out["holidays"]],
                         ["1. Weihnachtstag", "2. Weihnachtstag",
                          "Neujahrstag"])
        print("\nLIVE between 2026-12-24..2027-01-02: 3 holidays")

    def test_list_states_live(self):
        out = json.loads(srv.feiertage_list_states())
        self.assertEqual(out["count"], 17)
        codes = [s["code"] for s in out["states"]]
        self.assertIn("BE", codes)
        self.assertIn("NATIONAL", codes)
        print("\nLIVE states: 17")

    def test_bad_state_live(self):
        out = json.loads(srv.feiertage_list_holidays(2026, "XX"))
        self.assertIn("error", out)
        self.assertIn("unknown state", out["error"])

    def test_health_live(self):
        out = json.loads(srv.feiertage_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
        print(f"\nLIVE health: {out['status']} {out['http_status']}")


if __name__ == "__main__":
    unittest.main()
