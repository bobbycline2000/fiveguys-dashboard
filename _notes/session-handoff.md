# Session Handoff — 2026-04-20

## What we did this session
- Inventoried the cloud sandbox (Linux, `/home/user/fiveguys-dashboard`)
- Confirmed `main` branch was 20 commits behind the working branch `claude/organize-ai-setup-hfrhv`
- Fast-forward merged `claude/organize-ai-setup-hfrhv` → `main`
- Confirmed `main` is fully in sync with `origin/main` on GitHub — no push needed
- Gave Bobby the exact steps to clone this repo locally on Windows

## Current repo state
- **GitHub:** `https://github.com/bobbycline2000/fiveguys-dashboard`
- **Active branch for dev work:** `claude/organize-ai-setup-hfrhv`
- **Live dashboard branch:** `main` (auto-deploys to Netlify)
- **Working tree:** clean, nothing uncommitted

## What to do on first local session
1. `git clone https://github.com/bobbycline2000/fiveguys-dashboard.git`
2. `cd fiveguys-dashboard`
3. `copy .env.example .env` then fill in passwords (see CLAUDE.md for the full list)
4. `pip install -r scraper/requirements.txt`
5. `python -m playwright install chromium`
6. `python run.py` to test a manual scrape

## Secrets needed in .env (NOT in git)
| Variable | Status |
|---|---|
| `CRUNCHTIME_USERNAME` | Pre-filled: `BOBBY.CLINE` |
| `CRUNCHTIME_PASSWORD` | **You must fill this in** |
| `COMPLIANCEMATE_USERNAME` | Pre-filled: `FG2065@estep-co.com` |
| `COMPLIANCEMATE_PASSWORD` | **You must fill this in** |
| `MS_TENANT_ID` | **You must fill this in** (Azure Portal) |
| `MS_CLIENT_ID` | **You must fill this in** (Azure Portal) |
| `MS_CLIENT_SECRET` | **You must fill this in** (Azure Portal) |
| `STORE_ID` | Pre-filled: `2065` |

## Next priorities (pick up here)
- Confirm the ComplianceMate scraper (`scraper/scrape_compliancemate.py`) is working end-to-end
- Confirm the CrunchTime location picker is working (last known issue per CLAUDE.md)
- Consider scaffolding the multi-location architecture for the consulting product
