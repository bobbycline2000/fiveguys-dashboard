# Safe & Drawer Worker — One-Time Setup (5 steps, ~5 minutes)

Goal: spin up a free Cloudflare Worker that lets `safe_drawer.html` save
manager counts directly into the repo so every device shares one log.

> Each step is copy-paste. Do them in order in Windows PowerShell.

---

## Step 1 — Make a Cloudflare account (60 sec)

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with `bobby.cline2000@gmail.com` (or any email — Cloudflare is free for what we need).
3. Confirm the email link.

You do NOT need to add a domain. We're only using Workers.

---

## Step 2 — Make a GitHub Personal Access Token (PAT) (90 sec)

This token lets the worker commit `data/safe_drawer_log.json` to the repo.
It lives ONLY inside Cloudflare's secret store — never in any file.

1. Open https://github.com/settings/personal-access-tokens/new
2. **Token name:** `safe-drawer-worker`
3. **Resource owner:** bobbycline2000
4. **Expiration:** 1 year
5. **Repository access:** Only select repositories → `bobbycline2000/fiveguys-dashboard`
6. **Permissions → Repository permissions:**
   - **Contents:** Read and write
   - Everything else: leave at "No access"
7. Click **Generate token**.
8. **Copy the token now** (starts with `github_pat_...`). You won't see it again.

---

## Step 3 — Install wrangler + log in (90 sec)

In a fresh PowerShell window:

```powershell
npm install -g wrangler
wrangler login
```

A browser will open → click "Allow" → you'll see "Successfully logged in."

---

## Step 4 — Deploy the worker (60 sec)

In PowerShell:

```powershell
cd "C:\Users\bobby\OneDrive\BobbyWorkspace\github\fiveguys-dashboard\cloudflare-worker"
wrangler deploy
```

You'll see output that ends with:

```
Published safe-drawer-log
  https://safe-drawer-log.<your-subdomain>.workers.dev
```

**Copy that URL — that's the worker endpoint.** Looks like
`https://safe-drawer-log.bobbycline2000.workers.dev` (the subdomain is set
the first time you deploy a worker — Cloudflare will prompt you to pick one
if it's your first time).

---

## Step 5 — Set the two secrets (60 sec)

Still in the `cloudflare-worker` folder:

```powershell
wrangler secret put GITHUB_TOKEN
```

When it prompts, paste the `github_pat_...` token from Step 2. Press Enter.

Then:

```powershell
wrangler secret put SHARED_SECRET
```

When it prompts, paste any random string (e.g.
`safe-drawer-fg2065-2026`). Remember the exact string — you'll paste it
into `safe_drawer.html` in the next step.

---

## Step 6 — Tell the page where the worker is

Open `safe_drawer.html` in the repo root and find these two lines near
the top of the `<script>` block:

```js
const WORKER_URL = "";       // <-- paste worker URL from Step 4
const WORKER_SECRET = "";    // <-- paste SHARED_SECRET from Step 5
```

Paste in your two values. Save the file. Commit + push:

```powershell
cd "C:\Users\bobby\OneDrive\BobbyWorkspace\github\fiveguys-dashboard"
git add safe_drawer.html
git commit -m "wire safe_drawer.html to live worker"
git push
```

GitHub Pages refreshes in ~60 seconds. Open
https://bobbycline2000.github.io/fiveguys-dashboard/safe_drawer.html on
your phone, fill the form, hit **Save Today**. You should see:

- A green "Saved to live log ✓" flash.
- A new commit in the repo: `chore: safe-drawer log update by BC`.
- The Recent History table populates with everything every manager has
  ever saved across devices.

---

## How to know it's working

1. **From the page:** the saved flash says "Saved to live log ✓" instead
   of just "Saved" (which means localStorage fallback).
2. **From the repo:** check
   https://github.com/bobbycline2000/fiveguys-dashboard/commits/main —
   you'll see a commit per save, made by your PAT.
3. **From the brief:** tomorrow's 5 AM brief Deposits & Cash Counts
   section will show manager-submitted counts alongside the CrunchTime
   over/short.

## Troubleshooting

- **"unauthorized"** when saving → the `WORKER_SECRET` in the HTML
  doesn't match the `SHARED_SECRET` you set with wrangler. Re-run
  `wrangler secret put SHARED_SECRET` with the same string that's in the
  HTML, or edit the HTML to match.
- **"PUT file failed: 403"** → the GitHub PAT doesn't have
  `Contents: Read and write` on this repo. Regenerate it from Step 2.
- **The page still shows "Saved" not "Saved to live log ✓"** → the
  `WORKER_URL` is still empty in the HTML. Paste it in.

## Cost

Cloudflare Workers free tier: 100,000 requests/day. You'll use ~20/day.
Forever-free for this use case.
