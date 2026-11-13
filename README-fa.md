# feiertage-mcp 📅

mcp-name: io.github.mohammad-abbasi-sh/feiertage-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **تعطیلات رسمی آلمان** (gesetzliche Feiertage) از طریق [API سایت feiertage-api.de](https://feiertage-api.de) (پروژهٔ bundesAPI): تعطیلات هر سال در هر ایالت فدرال، بررسی اینکه یک تاریخ تعطیل است یا نه، نزدیک‌ترین تعطیل از یک تاریخ، و تعطیلات در یک بازهٔ زمانی. بدون کلید و بدون ورود.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP آلمان». وابسته به feiertage-api.de / پروژهٔ bundesAPI نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP Client اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m feiertage_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `feiertage_list_holidays` | تعطیلات رسمی یک سال در یک ایالت فدرال (با فیلتر اختیاری ماه) |
| `feiertage_is_holiday` | آیا یک تاریخ (YYYY-MM-DD) در یک ایالت تعطیل رسمی است؟ |
| `feiertage_next_holiday` | نزدیک‌ترین تعطیل رسمی از یک تاریخ به بعد (به سال بعد هم نگاه می‌کند) |
| `feiertage_holidays_between` | تعطیلات رسمی در یک بازهٔ زمانی (حداکثر حدود ۲ سال) |
| `feiertage_list_states` | هر ۱۶ ایالت فدرال + NATIONAL (تعطیلات سراسری) |
| `feiertage_health` | بررسی دسترسی به API (ok / blocked / error) — یک درخواست مؤدبانه |

نمونهٔ خروجی (`feiertage_is_holiday` / ۲۰۲۶-۱۰-۰۳، NATIONAL):

```json
{"date": "2026-10-03", "weekday": "Saturday", "weekday_de": "Samstag",
 "state": "NATIONAL", "is_holiday": true,
 "holidays": ["Tag der Deutschen Einheit"],
 "details": [{"name": "Tag der Deutschen Einheit", "date": "2026-10-03",
   "note": null, "note_only": false, "weekday": "Saturday",
   "weekday_de": "Samstag"}]}
```

نکته‌ها:
- کد ایالت‌ها دو حرفی است: BW، BY، BE، BB، HB، HH، HE، MV، NI، NW، RP، SL، SN، ST، SH، TH — یا `NATIONAL` برای تعطیلات سراسری (Neujahrstag، Karfreitag، Ostermontag، Tag der Arbeit، Christi Himmelfahrt، Pfingstmontag، Tag der Deutschen Einheit، ۱ و ۲ Weihnachtstag). فهرست کامل را از `feiertage_list_states` بگیرید.
- نام تعطیلات آلمانی است؛ هر تعطیلِ تاریخ‌دار روز هفته را هم به انگلیسی و هم به آلمانی دارد.
- چند ورودی تاریخ ندارند (`note_only: true`) — این‌ها فقط یادداشت‌اند، مثلاً روزهای تعطیل مدارس، نه تعطیل رسمی قانونی. ابزارهای مبتنی بر تاریخ آن‌ها را رد می‌کنند.
- سال‌های ۱۹۰۰ تا ۲۱۰۰ پذیرفته می‌شوند؛ API تقویم‌های گذشته و آینده را می‌دهد.
- `feiertage_holidays_between` برای هر سال در بازه یک درخواست می‌فرستد (حداکثر حدود ۲ سال).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
