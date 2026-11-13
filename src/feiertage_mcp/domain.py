"""Domain logic: shape feiertage-api.de responses into compact dicts
(stdlib only).

Data source: the free feiertage-api.de API — German public holidays
(gesetzliche Feiertage) per year and federal state, no key, no login.
The API is a thin wrapper over the German holiday calendar (Wikipedia /
feiertage-api.de, by the bundesAPI project).

- GET /api/?jahr=YYYY — all 16 federal states + NATIONAL, each a dict
  holiday name -> {"datum": "YYYY-MM-DD" or null, "hinweis": "..."}.
- GET /api/?jahr=YYYY&nur_land=XX — one state only (2-letter code, or
  NATIONAL for the nationwide holidays). Case-insensitive; an unknown
  code returns JSON `null` with HTTP 200.
- "datum" can be null: the entry is then a note only (e.g. Gründonnerstag
  in Baden-Württemberg 1990 — pupils have the day off, but it is not a
  statutory public holiday). Such entries are kept with date None and
  flagged note_only; date-based tools skip them.
- "hinweis" is a free-text note (often empty); kept as "note".

Holiday names are German (Neujahrstag, Karfreitag, ...); this server
does not translate them — the weekday is given in English and German.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from urllib.parse import quote_plus

BASE = "https://feiertage-api.de"

# The 16 federal states (Bundesländer) + NATIONAL (bundesweite Feiertage).
# Codes are the ones the API accepts in nur_land.
STATES = {
    "BW": "Baden-Württemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thüringen",
    "NATIONAL": "Bundesweit (nationwide)",
}

STATE_CODES = sorted(STATES)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_MIN, YEAR_MAX = 1900, 2100
MAX_RANGE_DAYS = 731  # holidays_between: at most ~2 years

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
               "Saturday", "Sunday"]
WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
               "Samstag", "Sonntag"]


def validate_year(year, default: int | None = None) -> int:
    """A year the API serves (1900..2100); default = current year."""
    if year is None:
        if default is None:
            default = date.today().year
        year = default
    try:
        y = int(year)
    except (TypeError, ValueError):
        raise ValueError(f"year must be a number, got {year!r}") from None
    if not YEAR_MIN <= y <= YEAR_MAX:
        raise ValueError(
            f"year out of range: {year} (expected {YEAR_MIN}..{YEAR_MAX})"
        )
    return y


def validate_state(state: str | None, default: str = "NATIONAL") -> str:
    """A 2-letter state code (case-insensitive) or NATIONAL."""
    if state is None:
        return default
    code = state.strip().upper()
    if code not in STATES:
        raise ValueError(
            f"unknown state {state!r} (expected one of: "
            + ", ".join(STATE_CODES) + ")"
        )
    return code


def validate_date(value: str) -> date:
    """A YYYY-MM-DD date."""
    text = (value or "").strip()
    if not DATE_RE.fullmatch(text):
        raise ValueError(
            f"bad date {value!r} (expected YYYY-MM-DD, e.g. 2026-12-25)"
        )
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"bad date {value!r} (not a real calendar date)") from None


def validate_month(month) -> int | None:
    """A month 1..12, or None (no month filter)."""
    if month is None:
        return None
    try:
        m = int(month)
    except (TypeError, ValueError):
        raise ValueError(f"month must be a number, got {month!r}") from None
    if not 1 <= m <= 12:
        raise ValueError(f"month out of range: {month} (expected 1..12)")
    return m


def holidays_url(year: int, state: str | None = None) -> str:
    """API URL for one year; state=None fetches all states at once."""
    y = validate_year(year)
    url = f"{BASE}/api/?jahr={y}"
    if state is not None:
        url += f"&nur_land={quote_plus(validate_state(state))}"
    return url


def _holiday_row(name: str, entry: dict) -> dict:
    datum = entry.get("datum")
    note = (entry.get("hinweis") or "").strip()
    row = {"name": name, "date": datum, "note": note or None,
           "note_only": datum is None}
    if datum:
        d = date.fromisoformat(datum)
        row["weekday"] = WEEKDAYS_EN[d.weekday()]
        row["weekday_de"] = WEEKDAYS_DE[d.weekday()]
    return row


def parse_holidays(text: str) -> list:
    """One state's holiday dict -> sorted list of holiday rows.

    Raises ValueError on JSON null (unknown state code) or bad shapes.
    Note-only entries (datum null) are kept, flagged note_only, and
    sort after dated entries.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid holidays response: {e}") from e
    if payload is None:
        raise ValueError(
            "unknown state code (the API returned null) — use one of: "
            + ", ".join(STATE_CODES)
        )
    if not isinstance(payload, dict):
        raise ValueError("unexpected holidays shape: not a JSON object")
    rows = []
    for name, entry in payload.items():
        if not isinstance(entry, dict) or "datum" not in entry:
            raise ValueError(f"unexpected holiday entry for {name!r}")
        rows.append(_holiday_row(name, entry))
    rows.sort(key=lambda r: (r["date"] is None, r["date"] or "", r["name"]))
    return rows


def parse_all_states(text: str) -> dict:
    """Full-year response -> {state_code: [holiday rows]}."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid holidays response: {e}") from e
    if not isinstance(payload, dict):
        raise ValueError("unexpected holidays shape: not a JSON object")
    out = {}
    for code, holidays in payload.items():
        if not isinstance(holidays, dict):
            raise ValueError(f"unexpected holidays shape for state {code!r}")
        out[code] = [
            _holiday_row(name, entry)
            for name, entry in holidays.items()
        ]
        out[code].sort(key=lambda r: (r["date"] is None, r["date"] or "",
                                      r["name"]))
    return out


def list_states() -> list:
    """All state codes with their German names (static data)."""
    return [{"code": code, "name": STATES[code]} for code in STATE_CODES]


def holidays_in_month(rows: list, month: int | None) -> list:
    """Filter dated holiday rows to one month (None = no filter)."""
    if month is None:
        return rows
    return [r for r in rows
            if r["date"] is not None and int(r["date"][5:7]) == month]


def is_holiday(rows: list, day: date) -> list:
    """Holiday rows falling on one date (dated entries only)."""
    target = day.isoformat()
    return [r for r in rows if r["date"] == target]


def next_holiday(rows: list, start: date) -> dict | None:
    """First dated holiday on or after `start`, or None."""
    target = start.isoformat()
    dated = [r for r in rows if r["date"] is not None]
    dated.sort(key=lambda r: r["date"])
    for row in dated:
        if row["date"] >= target:
            return row
    return None


def holidays_between(rows_by_year: dict[int, list], start: date,
                     end: date) -> list:
    """Merge per-year holiday rows into one dated, sorted list in range."""
    if end < start:
        raise ValueError(
            f"end date {end} is before start date {start}"
        )
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValueError(
            f"date range too wide: {(end - start).days} days "
            f"(max {MAX_RANGE_DAYS})"
        )
    out = []
    for year, rows in rows_by_year.items():
        for row in rows:
            if row["date"] is None:
                continue
            d = date.fromisoformat(row["date"])
            if start <= d <= end:
                out.append(row)
    out.sort(key=lambda r: r["date"])
    return out
