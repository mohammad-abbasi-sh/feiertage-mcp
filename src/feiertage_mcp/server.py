"""MCP server: unofficial read-only access to German public holidays via
the feiertage-api.de API (bundesAPI project) — holidays per year and
federal state, is-it-a-holiday checks, next holiday, date ranges and the
list of states. No key, no login.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for German public holidays (gesetzliche
Feiertage) — the feiertage-api.de API (bundesAPI project): holidays per
year and federal state (Bundesland), is-it-a-holiday checks, the next
holiday from a date, and holidays in a date range. No key, no login.
State codes are the 2-letter codes (BW, BY, BE, BB, HB, HH, HE, MV, NI,
NW, RP, SL, SN, ST, SH, TH) or NATIONAL for the nationwide holidays
(Neujahrstag, Karfreitag, Ostermontag, Tag der Arbeit, Christi
Himmelfahrt, Pfingstmontag, Tag der Deutschen Einheit, 1./2.
Weihnachtstag). Holiday names are German; each dated holiday also
carries its weekday (English + German). A few entries have no date
(note_only: true) — they are notes, e.g. school-free days, not statutory
holidays.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — \
Germany MCP factory.
"""

_SOURCE = "feiertage-api.de (bundesAPI project)"
_DISCLAIMER = "Unofficial read-only data from feiertage-api.de; verify on feiertage-api.de before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _fetch_year(year: int, state: str) -> list:
    """Holiday rows for one year + state (live fetch + parse)."""
    return _dom.parse_holidays(
        _http.fetch_text(_dom.holidays_url(year, state)))


mcp = FastMCP("feiertage-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
def feiertage_list_holidays(year: int | None = None,
                            state: str = "NATIONAL",
                            month: int | None = None) -> str:
    """List the public holidays of one year in one German federal state.
    year: e.g. 2026 (default: current year). state: 2-letter code
    (BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH)
    or NATIONAL for the nationwide holidays (default NATIONAL).
    month: 1..12 to filter to one month (default: whole year).
    Entries with date null (note_only) are notes, not statutory holidays."""
    try:
        y = _dom.validate_year(year)
        code = _dom.validate_state(state)
        m = _dom.validate_month(month)
        rows = _dom.holidays_in_month(_fetch_year(y, code), m)
    except (_http.FeiertageMcpError, ValueError) as e:
        return _err(e)
    return _ok({"year": y, "state": code, "state_name": _dom.STATES[code],
                "month": m, "count": len(rows), "holidays": rows})


@mcp.tool()
def feiertage_is_holiday(day: str, state: str = "NATIONAL") -> str:
    """Is a date a public holiday in one German federal state?
    day: YYYY-MM-DD, e.g. 2026-12-25. state: 2-letter code or NATIONAL
    (default NATIONAL). Returns is_holiday plus the holiday name(s)."""
    try:
        d = _dom.validate_date(day)
        code = _dom.validate_state(state)
        rows = _dom.is_holiday(_fetch_year(d.year, code), d)
    except (_http.FeiertageMcpError, ValueError) as e:
        return _err(e)
    return _ok({"date": d.isoformat(), "weekday": _dom.WEEKDAYS_EN[d.weekday()],
                "weekday_de": _dom.WEEKDAYS_DE[d.weekday()],
                "state": code, "state_name": _dom.STATES[code],
                "is_holiday": bool(rows),
                "holidays": [r["name"] for r in rows],
                "details": rows})


@mcp.tool()
def feiertage_next_holiday(from_date: str | None = None,
                           state: str = "NATIONAL") -> str:
    """The next public holiday on or after a date in one German state.
    from_date: YYYY-MM-DD (default: today). state: 2-letter code or
    NATIONAL (default NATIONAL). Looks into the next year if the
    current year has no holiday left."""
    try:
        start = (_dom.validate_date(from_date) if from_date
                 else date.today())
        code = _dom.validate_state(state)
        row = _dom.next_holiday(_fetch_year(start.year, code), start)
        year = start.year
        if row is None:
            year = start.year + 1
            row = _dom.next_holiday(_fetch_year(year, code), start)
    except (_http.FeiertageMcpError, ValueError) as e:
        return _err(e)
    if row is None:
        return _ok({"from_date": start.isoformat(), "state": code,
                    "state_name": _dom.STATES[code],
                    "next_holiday": None})
    return _ok({"from_date": start.isoformat(), "state": code,
                "state_name": _dom.STATES[code], "year": year,
                "next_holiday": row})


@mcp.tool()
def feiertage_holidays_between(start_date: str, end_date: str,
                               state: str = "NATIONAL") -> str:
    """Public holidays in a date range in one German federal state.
    start_date / end_date: YYYY-MM-DD (max range ~2 years).
    state: 2-letter code or NATIONAL (default NATIONAL)."""
    try:
        start = _dom.validate_date(start_date)
        end = _dom.validate_date(end_date)
        code = _dom.validate_state(state)
        rows_by_year = {
            y: _fetch_year(y, code)
            for y in range(start.year, end.year + 1)
        }
        rows = _dom.holidays_between(rows_by_year, start, end)
    except (_http.FeiertageMcpError, ValueError) as e:
        return _err(e)
    return _ok({"start_date": start.isoformat(),
                "end_date": end.isoformat(), "state": code,
                "state_name": _dom.STATES[code], "count": len(rows),
                "holidays": rows})


@mcp.tool()
def feiertage_list_states() -> str:
    """All 16 German federal states (Bundesländer) plus NATIONAL
    (nationwide holidays) — the state codes the other tools accept."""
    return _ok({"count": len(_dom.STATES),
                "states": _dom.list_states()})


@mcp.tool()
def feiertage_health() -> str:
    """Check whether the feiertage-api.de API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
