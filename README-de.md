# feiertage-mcp 📅

mcp-name: io.github.mohammad-abbasi-sh/feiertage-mcp

Inoffizieller **Nur-Lesen**-MCP-Server für **deutsche Feiertage** (gesetzliche Feiertage) über die [feiertage-api.de API](https://feiertage-api.de) (bundesAPI-Projekt): Feiertage pro Jahr und Bundesland, Ist-es-ein-Feiertag-Prüfung, der nächste Feiertag ab einem Datum und Feiertage in einem Zeitraum. Kein Schlüssel, keine Anmeldung nötig.

> Gebaut von Mohammad Abbasi im Rahmen der „Germany MCP factory". Keine Verbindung zu feiertage-api.de / dem bundesAPI-Projekt.

## Für KI-Agenten

In die MCP-Client-Konfiguration eintragen (stdio):

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

Oder lokal starten: `python -m feiertage_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|--------------|
| `feiertage_list_holidays` | Feiertage eines Jahres in einem Bundesland (optional nach Monat gefiltert) |
| `feiertage_is_holiday` | Ist ein Datum (YYYY-MM-DD) ein Feiertag in einem Bundesland? |
| `feiertage_next_holiday` | Der nächste Feiertag ab einem Datum (blickt auch ins nächste Jahr) |
| `feiertage_holidays_between` | Feiertage in einem Zeitraum (max. ca. 2 Jahre) |
| `feiertage_list_states` | Alle 16 Bundesländer + NATIONAL (bundesweite Feiertage) |
| `feiertage_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

Beispielausgabe (`feiertage_is_holiday` / 2026-10-03, NATIONAL):

```json
{"date": "2026-10-03", "weekday": "Saturday", "weekday_de": "Samstag",
 "state": "NATIONAL", "is_holiday": true,
 "holidays": ["Tag der Deutschen Einheit"],
 "details": [{"name": "Tag der Deutschen Einheit", "date": "2026-10-03",
   "note": null, "note_only": false, "weekday": "Saturday",
   "weekday_de": "Samstag"}]}
```

Hinweise:
- Bundesland-Codes sind die 2-Buchstaben-Codes: BW, BY, BE, BB, HB, HH, HE, MV, NI, NW, RP, SL, SN, ST, SH, TH — oder `NATIONAL` für die bundesweiten Feiertage (Neujahrstag, Karfreitag, Ostermontag, Tag der Arbeit, Christi Himmelfahrt, Pfingstmontag, Tag der Deutschen Einheit, 1./2. Weihnachtstag). `feiertage_list_states` liefert die vollständige Liste.
- Feiertagsnamen sind deutsch; jeder datierte Feiertag trägt zusätzlich seinen Wochentag auf Englisch und Deutsch.
- Einige Einträge haben kein Datum (`note_only: true`) — das sind Hinweise, z. B. schulfreie Tage, keine gesetzlichen Feiertage. Datumsbasierte Tools überspringen sie.
- Jahre 1900–2100 werden akzeptiert; die API liefert historische und zukünftige Kalender.
- `feiertage_holidays_between` stellt eine Anfrage pro Jahr im Zeitraum (max. ca. 2 Jahre).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
