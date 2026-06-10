#!/usr/bin/env python3
"""
indeed_hiring.py — Five Guys Dixie Highway (KY-2065) hiring pipeline.

Pull management applicants (AGM + Shift Leader) from Indeed for Employers,
vet by work history, emit data/indeed_applicants.json for the dashboard Hiring page,
and (optionally) batch-send interview invites via the sendConversationEvent API.

ARCHITECTURE — see scraper/INDEED_API.md for the full endpoint map.
Indeed auth is session-scoped (cookie + indeed-api-key + indeed-ctk headers).
This script does NOT log in. The indeed-hiring agent captures a live session from a
logged-in Chrome tab and writes it to a tokens file (default: data/indeed_session.json):

    {
      "url": "https://apis.indeed.com/graphql?co=US&locale=en-US",
      "headers": { "accept": "...", "content-type": "...",
                   "indeed-api-key": "...", "indeed-ctk": "...",
                   "indeed-client-sub-app": "...", "indeed-client-sub-app-component": "..." },
      "cookies": { ... },            # employer session cookies
      "advertiser_key": "<32-char constant for fg2079 / 737 Ventures>",
      "send_template": { ...captured sendConversationEvent request body... },
      "contact_template": { ...captured legacyIds filter-query request body... }
    }

Because Indeed gates employer login behind MFA, the token-capture step runs through the
agent's Chrome session (same pattern as the Outlook MSAL grab). Once tokens are fresh,
every call here is pure requests — no browser at runtime.
"""

import json, os, sys, uuid, time, argparse, datetime
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SESSION_FILE = os.path.join(DATA, "indeed_session.json")
OUT_FILE = os.path.join(DATA, "indeed_applicants.json")

STORE = "Five Guys Dixie Highway (KY-2065)"
ADDRESS = "9050 Dixie Hwy, Louisville, KY 40258"
HIRING_MANAGER = "Bobby"
TARGET_ROLES = ("Assistant General Manager", "AGM", "General Manager", "Shift Leader", "Shift Manager")
EXCLUDE_ROLES = ("Crew Member",)
INTERVIEW_CADENCE = "Mondays + Thursdays"

MGMT_TITLE_RE = ("manager", "supervisor", "lead", "agm", "assistant manager",
                 "general manager", "shift", "director", "owner", "foreman")

MESSAGE = (
    "Hi {first} - this is {hm}, hiring manager at Five Guys Dixie Highway, "
    "{addr}. Thanks for applying. I'd like to meet you for an in-person interview "
    "{when}. Please bring two forms of ID. Reply here to confirm you'll be there. - {hm}"
)


def load_session(path=SESSION_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _post(sess, body):
    return requests.post(sess["url"], headers=sess["headers"],
                         cookies=sess.get("cookies"), json=body, timeout=30)


# ---- PULL -------------------------------------------------------------------
def pull_candidates(sess, legacy_ids=None, include_all_statuses=False):
    """Batch contact/details query. Returns list of dicts: name, phone, legacy_id, job_key, role."""
    body = json.loads(json.dumps(sess["contact_template"]))
    b = body[0] if isinstance(body, list) else body
    flt = b["variables"]["input"]["filter"]
    if legacy_ids is not None:
        flt["legacyIds"] = legacy_ids
    if include_all_statuses:
        flt.pop("hiringMilestones", None)
    if "first" in b["variables"]:
        b["variables"]["first"] = 100
    r = _post(sess, body)
    r.raise_for_status()
    j = r.json()
    out = {}

    def walk(o):
        if isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            if o.get("__typename") == "IndeedApplyCandidateSubmission" or "legacyID" in o:
                leg = o.get("legacyID")
                name = (((o.get("profile") or {}).get("name") or {}).get("displayName"))
                phone = (((o.get("profile") or {}).get("contact") or {}).get("phoneNumber"))
                job_key, title = _find_job(o)
                if leg:
                    out[leg] = {"legacy_id": leg, "name": name, "phone": phone,
                                "job_key": job_key, "role": title}
            for v in o.values():
                walk(v)
    walk(j)
    return list(out.values())


def _find_job(node):
    found = {"k": None, "t": None}

    def dig(x):
        if found["k"]:
            return
        if isinstance(x, dict):
            if "jobKey" in x:
                found["k"] = x["jobKey"]
                found["t"] = x.get("title")
                return
            for v in x.values():
                dig(v)
        elif isinstance(x, list):
            for v in x:
                dig(v)
    dig(node)
    return found["k"], found["t"]


def is_mgmt(role):
    r = (role or "").lower()
    if any(x.lower() in r for x in EXCLUDE_ROLES):
        return False
    return any(x.lower() in r for x in TARGET_ROLES)


def vet(applicant, experience):
    """Score by management history. experience = [{company,title,dateRange}]."""
    score = 0
    role = (applicant.get("role") or "")
    if "AGM" in role or "Assistant General Manager" in role or "General Manager" in role:
        score += 3
    mgmt_jobs = [e for e in experience if any(m in (e.get("title") or "").lower() for m in MGMT_TITLE_RE)]
    score += 2 * len(mgmt_jobs)
    if len(experience) >= 3:
        score += 1
    if len(experience) == 0:
        score -= 2
    tier = "strong" if score >= 4 else "mid" if score >= 2 else "weak"
    return tier, score, [e.get("title") for e in mgmt_jobs]


# ---- SEND -------------------------------------------------------------------
def send_invite(sess, legacy_id, job_key, first_name, when):
    tpl = json.loads(json.dumps(sess["send_template"]))
    b = tpl[0] if isinstance(tpl, list) else tpl
    v = b["variables"]
    v["messageBody"] = MESSAGE.format(first=first_name, hm=HIRING_MANAGER, addr=ADDRESS, when=when)
    scope = v["context"]["scope"]["preOrPostApply"]
    scope["advertiserKey"] = sess["advertiser_key"]
    scope["candidateKey"] = legacy_id           # candidateKey == legacyId
    scope["aggJobKey"] = job_key                # aggJobKey == applied job's jobKey
    if "correlationKey" in v:
        v["correlationKey"] = str(uuid.uuid4())
    if "eventId" in v:
        v["eventId"] = str(uuid.uuid4())
    r = _post(sess, tpl)
    j = r.json()
    ok = (r.status_code == 200) and not j.get("errors") and "sendConversationEvent" in json.dumps(j)
    return ok, (json.dumps(j.get("errors"))[:200] if j.get("errors") else None)


def send_batch(sess, shortlist, when, pause=0.7):
    results = []
    for a in shortlist:
        ok, err = send_invite(sess, a["legacy_id"], a["job_key"],
                              (a["name"] or "there").split()[0], when)
        results.append({"name": a["name"], "ok": ok, "err": err})
        time.sleep(pause)
    return results


# ---- DASHBOARD OUTPUT -------------------------------------------------------
def write_dashboard(applicants, invited_names, when):
    agm = sum(1 for a in applicants if "AGM" in (a.get("role") or "") or "Assistant General Manager" in (a.get("role") or ""))
    out = {
        "generated": datetime.date.today().isoformat(),
        "store": STORE, "address": ADDRESS, "window_days": 5,
        "roles_targeted": ["Assistant General Manager (AGM)", "Shift Leader"],
        "interview_cadence": INTERVIEW_CADENCE, "next_interviews": when,
        "summary": {"total_mgmt_applicants": len(applicants), "agm": agm,
                    "shift_leader": len(applicants) - agm, "invited": len(invited_names)},
        "applicants": [{
            "name": a["name"],
            "role": "AGM" if ("AGM" in (a.get("role") or "") or "Assistant General Manager" in (a.get("role") or "")) else "Shift Leader",
            "location": a.get("location", ""), "applied": a.get("applied", ""),
            "phone": a.get("phone", ""), "tier": a.get("tier", "mid"),
            "invited": a["name"] in invited_names, "history": a.get("history", "")
        } for a in applicants]
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return OUT_FILE


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Indeed hiring pipeline for Five Guys Dixie Highway")
    p.add_argument("--session", default=SESSION_FILE, help="path to captured session/tokens json")
    p.add_argument("--send", action="store_true", help="actually send invites to the vetted shortlist")
    p.add_argument("--when", default="Thursday, anytime between 1:00 and 4:00 PM",
                   help="interview window string for the message")
    p.add_argument("--legacy-ids", nargs="*", help="explicit legacyIds to target")
    args = p.parse_args()

    if not os.path.exists(args.session):
        sys.exit(f"No session file at {args.session}. Have the indeed-hiring agent capture a live session first.")

    sess = load_session(args.session)
    cands = [c for c in pull_candidates(sess, legacy_ids=args.legacy_ids, include_all_statuses=True) if is_mgmt(c.get("role"))]
    print(f"Pulled {len(cands)} management applicants.")
    # NOTE: experience-based vetting requires the FindRCPMatches harvest (see INDEED_API.md);
    # the agent supplies experience per legacy_id. Here we mark all as mid by default.
    if args.send:
        shortlist = [c for c in cands if c.get("tier") == "strong" and c.get("job_key")]
        res = send_batch(sess, shortlist, args.when)
        for r in res:
            print(("  OK   " if r["ok"] else "  FAIL ") + str(r["name"]) + (f"  {r['err']}" if r["err"] else ""))
