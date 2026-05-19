# BOSS — Bread Ordering Subscriber System

**URL:** `https://bread2.fiveguys.com`
**Tech:** PHP app, jQuery 1.7.2 (~2012 vintage). No JSON API — calendar is server-rendered HTML.
**Auth:** form POST to `index.php` → PHP session cookie (`PHPSESSID`).

## Auth

- Login form on `https://bread2.fiveguys.com/index.php`
- Method: POST, content-type `application/x-www-form-urlencoded`
- Fields (standard PHP — confirmed on first run):
  - `username` (Bobby's store login is `Louisville.2065`)
  - `password`
- Successful login → 302 redirect to `orders.php` and sets `PHPSESSID` cookie
- Session expires after inactivity; safest pattern is fresh login per scrape run (it's a cheap POST)

## Calendar endpoint

- **URL:** `https://bread2.fiveguys.com/orders.php` (GET, cookie-authed)
- **Returns:** full HTML page with `<table id="calendar">` containing 5–6 weeks of cells
- Header text like `May / June` indicates the month range shown
- No date-range query params — server picks the window. Typically: yesterday → ~6 weeks forward.

## Cell parsing (one `<td>` per day)

```html
<td class="future_date holiday">
  <div class="date_number">26</div>
  <div class="details">
    5 HB Tray5Bag
    1 HD Tray6Bag
    <img src="images/modify.gif" alt="Adjust Order">
    Web Submitted Order
    Louisville.2065 05/12/2026
  </div>
</td>
```

### Cell classes

| Class | Meaning |
|---|---|
| `past_date` | historical (read-only, may still show delivered qty) |
| `future_date` | upcoming, normal day |
| `future_date holiday` | upcoming + part of a holiday-shifted week |

### Cell signals (parse from `innerHTML`)

| Signal | Source |
|---|---|
| Day-of-month | `.date_number` innerText |
| HB tray count | regex `(\d+)\s*HB` on cell text |
| HD tray count | regex `(\d+)\s*HD` on cell text |
| Submission date | regex `(\d{2}/\d{2}/\d{4})` |
| Holiday | `cls.includes('holiday')` OR `getComputedStyle(td).backgroundImage` includes `holiday` |
| In transit (locked) | `<img src=".../transit.gif">` |
| Adjust available | `<img src=".../modify.gif">` |
| Place needed (empty slot) | `<img src=".../order.gif">` |
| Reported issue | `<img src=".../Bread_Issue_Buttonrev5.gif">` |
| Skipped delivery day | future_date cell with NO HB/HD value AND no `order.gif` icon |

## Holiday-week pattern (observed Memorial Day 2026)

```
Mon 5/25 — future_date              (BLANK = holiday skip)
Tue 5/26 — future_date holiday      (5 HB / 1 HD — substitution for Mon)
Wed 5/27 — future_date holiday      (8 HB / 0 HD)
Thu 5/28 — future_date              (BLANK = normal off-day)
Fri 5/29 — future_date holiday      (7 HB / 1 HD)
Sat 5/30 — future_date holiday      (11 HB / 0 HD)
```

**Detection rule for a "holiday week"**: any `<td class="future_date holiday">` cell in the calendar — those flag the entire delivery week as shifted. The blank Mon adjacent to a holiday week is the skipped delivery.

## Known FG holiday weeks per year (~6)

- Memorial Day (last Mon of May)
- Independence Day (Jul 4)
- Labor Day (first Mon of Sep)
- Thanksgiving (4th Thu of Nov)
- Christmas (Dec 25)
- New Year's Day (Jan 1)

## Other pages (not yet scraped)

| Path | Purpose |
|---|---|
| `order_view.php` | Past order history grid |
| `invoices.php` | Invoice list |
| `issues_view.php` | Bread issue tickets |
| `reports_zero_qty.php` | Zero-qty report |

## Discovery date

2026-05-19 — reverse-engineered via Chrome MCP while Bobby was logged in. Bobby's store profile: User ID `Louisville.2065`, Bakery `Alpha - Ohio Valley`, Route `AOV01`.
