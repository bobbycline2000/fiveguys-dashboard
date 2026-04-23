# Data directory

Three zones. Each has a specific job. Do not mix.

## `raw/` — exactly what the scraper saw (audit trail)

```
raw/<source>/<store_id>/<YYYY-MM-DD>/<report>.json
raw/<source>/<store_id>/<YYYY-MM-DD>/<report>.pdf      (if native export)
raw/<source>/<store_id>/<YYYY-MM-DD>/page_source.html  (debug, gitignored)
```

**Never overwrite.** Never delete. One folder per date, per store, per source. This is the
forensic record — if a scraped number looks wrong three months from now, we can open the raw
file and see exactly what the source showed.

Sources in use today:
- `crunchtime/` — Net Chef Performance Metrics, COGS variance widget
- `parbrink/` — Weekly Labor Schedule, Sales export, Deposits
- `compliancemate/` — daily list scores
- `marketforce/` — secret shop scores

## `normalized/` — append-only, one row per day per store per metric

```
normalized/<metric>/<store_id>.jsonl
```

One JSON object per line. Built by `normalize.py` (not yet written) from the raw/ files.
This is what historical queries run against.

## `dashboard/` — the single file the HTML reads

```
dashboard/<store_id>/latest.json
```

Pre-computed, small, fast. The dashboard HTML reads nothing else. Regenerated on every scrape.

---

## Legacy top-level files (pre-migration)

These still exist and are still written as backward-compat:
- `latest.json` → moved to `raw/crunchtime/2065/<date>/perf_metrics.json`
- `compliancemate.json` → `raw/compliancemate/2065/<date>/lists.json`
- `secret_shops.json` → `raw/marketforce/2065/<date>/shops.json`
- `cogs_variance.json` → `raw/crunchtime/2065/<week_end>/cogs_variance.json`
- `parbrink/<date>/weekly_schedule_2065.json` → `raw/parbrink/2065/<date>/weekly_schedule.json`

Will be removed once all scrapers + readers point at the new paths.
