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

async function ghGetFile(token) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}?ref=${BRANCH}`;
  const r = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept:        "application/vnd.github+json",
      "User-Agent":  "safe-drawer-worker",
    },
  });
  if (r.status === 404) return { sha: null, rows: [] };
  if (!r.ok) throw new Error(`GET file failed: ${r.status}`);
  const data = await r.json();
  const raw = atob(data.content.replace(/\n/g, ""));
  let rows;
  try { rows = JSON.parse(raw); } catch { rows = []; }
  if (!Array.isArray(rows)) rows = [];
  return { sha: data.sha, rows };
}

async function ghPutFile(token, sha, rows, manager) {
  const url = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`;
  const body = {
    message: `chore: safe-drawer log update by ${manager || "manager"}`,
    content: btoa(JSON.stringify(rows, null, 2)),
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
    throw new Error(`PUT file failed: ${r.status} ${t}`);
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
  out.bag        = str(payload.bag, 30);
  out.deposit    = num(payload.deposit);
  out.safe_open  = num(payload.safe_open);
  out.d1_open    = num(payload.d1_open);
  out.d2_open    = num(payload.d2_open);
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
        const { rows } = await ghGetFile(env.GITHUB_TOKEN);
        return json({ ok: true, rows });
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
        const { sha, rows } = await ghGetFile(env.GITHUB_TOKEN);
        // Idempotent per (date, mgr): replace any prior row from same manager on same date.
        const key = (r) => `${r.date}::${(r.mgr || "").toUpperCase()}`;
        const k = key(clean);
        const filtered = rows.filter((r) => key(r) !== k);
        filtered.push(clean);
        filtered.sort((a, b) => (a.date || "").localeCompare(b.date || ""));
        // Keep last 400 entries.
        const trimmed = filtered.slice(-400);
        await ghPutFile(env.GITHUB_TOKEN, sha, trimmed, clean.mgr);
        return json({ ok: true, entry: clean, total: trimmed.length });
      } catch (e) {
        return json({ ok: false, error: String(e) }, 500);
      }
    }

    return json({ ok: false, error: "not found" }, 404);
  },
};
