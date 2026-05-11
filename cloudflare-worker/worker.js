/**
 * Safe & Drawer Log — Cloudflare Worker
 *
 * Public endpoint the safe_drawer.html page calls when a manager hits Save.
 * Writes the submitted form entry into data/safe_drawer_log.json in the
 * GitHub repo `bobbycline2000/fiveguys-dashboard` on the main branch.
 *
 * Secrets (set via `wrangler secret put`):
 *   - GITHUB_TOKEN   PAT with `contents:write` scope on this repo
 *   - SHARED_SECRET  Random string the HTML page must include in the POST
 *                    body so random visitors can't spam the endpoint.
 *
 * Endpoints:
 *   GET  /log       → returns the current JSON log (for the page history view)
 *   POST /submit    → accepts one form submission, commits to repo
 *   OPTIONS *       → CORS preflight
 */

const REPO_OWNER = "bobbycline2000";
const REPO_NAME  = "fiveguys-dashboard";
const FILE_PATH  = "data/safe_drawer_log.json";
const PENDING_PATH = "data/deposits_pending.json";
const BRANCH     = "main";

const CORS = {
  "Access-Control-Allow-Origin":  "https://bobbycline2000.github.io",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age":       "86400",
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS, ...extra },
  });
}

async function ghGetFile(token, path = FILE_PATH, { fallback = [] } = {}) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}?ref=${BRANCH}`;
  const r = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept:        "application/vnd.github+json",
      "User-Agent":  "safe-drawer-worker",
    },
  });
  if (r.status === 404) return { sha: null, data: fallback };
  if (!r.ok) throw new Error(`GET ${path} failed: ${r.status}`);
  const meta = await r.json();
  const raw = atob(meta.content.replace(/\n/g, ""));
  let data;
  try { data = JSON.parse(raw); } catch { data = fallback; }
  return { sha: meta.sha, data };
}

async function ghPutFile(token, path, sha, data, message) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${path}`;
  const body = {
    message: message || `chore: ${path} update`,
    content: btoa(JSON.stringify(data, null, 2)),
    branch:  BRANCH,
    ...(sha ? { sha } : {}),
  };
  const r = await fetch(url, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept:        "application/vnd.github+json",
      "User-Agent":  "safe-drawer-worker",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`PUT ${path} failed: ${r.status} ${t}`);
  }
  return await r.json();
}

function sanitize(payload) {
  // Whitelist fields + clamp lengths so we never commit junk.
  const out = {};
  const str = (v, max = 200) => (typeof v === "string" ? v.trim().slice(0, max) : "");
  const num = (v) => {
    const n = parseFloat(v);
    return Number.isFinite(n) ? Math.round(n * 100) / 100 : 0;
  };
  out.date       = str(payload.date, 12);
  out.mgr        = str(payload.mgr, 8);
  out.deposit    = num(payload.deposit);
  out.safe_open  = num(payload.safe_open);
  out.d1_open    = num(payload.d1_open);
  out.d2_open    = num(payload.d2_open);
  out.safe_mid   = num(payload.safe_mid);
  out.d1_mid     = num(payload.d1_mid);
  out.d2_mid     = num(payload.d2_mid);
  out.safe_close = num(payload.safe_close);
  out.d1_close   = num(payload.d1_close);
  out.d2_close   = num(payload.d2_close);
  out.ct_os      = num(payload.ct_os);
  out.notes      = str(payload.notes, 500);
  out.submitted_at = new Date().toISOString();
  return out;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });

    if (req.method === "GET" && url.pathname === "/log") {
      try {
        const { data } = await ghGetFile(env.GITHUB_TOKEN, FILE_PATH, { fallback: [] });
        return json({ ok: true, rows: Array.isArray(data) ? data : [] });
      } catch (e) {
        return json({ ok: false, error: String(e) }, 500);
      }
    }

    if (req.method === "GET" && url.pathname === "/deposits-pending") {
      try {
        const { data } = await ghGetFile(env.GITHUB_TOKEN, PENDING_PATH,
          { fallback: { pending: [], processed: [] } });
        return json({ ok: true, state: data });
      } catch (e) {
        return json({ ok: false, error: String(e) }, 500);
      }
    }

    if (req.method === "POST" && url.pathname === "/submit") {
      let body;
      try { body = await req.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }

      if (!body || body.secret !== env.SHARED_SECRET) {
        return json({ ok: false, error: "unauthorized" }, 401);
      }
      if (!body.entry || !body.entry.date) {
        return json({ ok: false, error: "missing date" }, 400);
      }
      const clean = sanitize(body.entry);

      try {
        const { sha, data } = await ghGetFile(env.GITHUB_TOKEN, FILE_PATH, { fallback: [] });
        const rows = Array.isArray(data) ? data : [];
        // Idempotent per date: any save for the same business date replaces the
        // existing row — so opening / mid / nightly across multiple managers
        // merge into one row per day instead of duplicating.
        const filtered = rows.filter((r) => r.date !== clean.date);
        filtered.push(clean);
        filtered.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
        const trimmed = filtered.slice(-400);
        await ghPutFile(env.GITHUB_TOKEN, FILE_PATH, sha, trimmed,
          `chore: safe-drawer log update by ${clean.mgr || "manager"}`);
        return json({ ok: true, entry: clean, total: trimmed.length });
      } catch (e) {
        return json({ ok: false, error: String(e) }, 500);
      }
    }

    if (req.method === "POST" && url.pathname === "/enter-deposit") {
      let body;
      try { body = await req.json(); } catch { return json({ ok: false, error: "bad json" }, 400); }
      if (!body || body.secret !== env.SHARED_SECRET) {
        return json({ ok: false, error: "unauthorized" }, 401);
      }
      const num = (v) => {
        const n = parseFloat(v);
        return Number.isFinite(n) ? Math.round(n * 100) / 100 : NaN;
      };
      const str = (v, max = 200) => (typeof v === "string" ? v.trim().slice(0, max) : "");
      const business_date = str(body.business_date, 12);  // ISO YYYY-MM-DD
      const amount        = num(body.amount);
      const mgr           = str(body.mgr, 8);
      const memo          = str(body.memo, 200);

      if (!/^\d{4}-\d{2}-\d{2}$/.test(business_date)) {
        return json({ ok: false, error: "business_date must be YYYY-MM-DD" }, 400);
      }
      if (!Number.isFinite(amount) || amount <= 0) {
        return json({ ok: false, error: "amount must be > 0" }, 400);
      }

      const entry = {
        id: crypto.randomUUID(),
        business_date,
        amount,
        memo,
        mgr,
        requested_at: new Date().toISOString(),
      };

      try {
        const { sha, data } = await ghGetFile(env.GITHUB_TOKEN, PENDING_PATH,
          { fallback: { pending: [], processed: [] } });
        const state = (data && typeof data === "object") ? data : { pending: [], processed: [] };
        if (!Array.isArray(state.pending))   state.pending   = [];
        if (!Array.isArray(state.processed)) state.processed = [];

        // Idempotent per business_date: a second request for the same date
        // replaces the older pending entry.
        state.pending = state.pending.filter((p) => p.business_date !== business_date);
        state.pending.push(entry);

        await ghPutFile(env.GITHUB_TOKEN, PENDING_PATH, sha, state,
          `chore: deposit entry requested — ${business_date} $${amount} by ${mgr || "?"}`);
        return json({ ok: true, queued: entry,
          message: "Deposit queued. Agent will enter in CT within ~1 hour." });
      } catch (e) {
        return json({ ok: false, error: String(e) }, 500);
      }
    }

    return json({ ok: false, error: "not found" }, 404);
  },
};
