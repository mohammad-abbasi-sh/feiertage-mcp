# feiertage-mcp 📅

mcp-name: io.github.mohammad-abbasi-sh/feiertage-mcp

Unofficial **read-only** MCP server for **German public holidays** (gesetzliche Feiertage) via the [feiertage-api.de API](https://feiertage-api.de) (bundesAPI project): holidays per year and federal state, is-it-a-holiday checks, the next holiday from a date, and holidays in a date range. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with feiertage-api.de / the bundesAPI project.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "feiertage": {
      "command": "uvx",
      "args": ["feiertage-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m feiertage_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `feiertage_list_holidays` | Public holidays of one year in one federal state (optional month filter) |
| `feiertage_is_holiday` | Is a date (YYYY-MM-DD) a public holiday in one state? |
| `feiertage_next_holiday` | The next public holiday on or after a date (looks into the next year) |
| `feiertage_holidays_between` | Public holidays in a date range (max ~2 years) |
| `feiertage_list_states` | All 16 federal states + NATIONAL (nationwide holidays) |
| `feiertage_health` | Reachability check (ok / blocked / error) — one polite request |

Example output (`feiertage_is_holiday` / 2026-10-03, NATIONAL):

```json
{"date": "2026-10-03", "weekday": "Saturday", "weekday_de": "Samstag",
 "state": "NATIONAL", "is_holiday": true,
 "holidays": ["Tag der Deutschen Einheit"],
 "details": [{"name": "Tag der Deutschen Einheit", "date": "2026-10-03",
   "note": null, "note_only": false, "weekday": "Saturday",
   "weekday_de": "Samstag"}]}
```

Notes:
- State codes are the 2-letter codes: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH — or `NATIONAL` for the nationwide holidays (Neujahrstag, Karfreitag, Ostermontag, Tag der Arbeit, Christi Himmelfahrt, Pfingstmontag, Tag der Deutschen Einheit, 1./2. Weihnachtstag). Use `feiertage_list_states` for the full list.
- Holiday names are German; each dated holiday also carries its weekday in English and German.
- A few entries have no date (`note_only: true`) — they are notes, e.g. school-free days, not statutory public holidays. Date-based tools skip them.
- Years 1900–2100 are accepted; the API serves historical and future calendars.
- `feiertage_holidays_between` fetches one request per year in the range (max ~2 years).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
