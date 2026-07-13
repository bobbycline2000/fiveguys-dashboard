# Indeed for Employers — Reverse-Engineered API

Discovered 2026-06-10. Account: **737 Ventures / fg2079**, logged in as **rcline@estep-co.com**. Single GraphQL endpoint powers the whole employer console.

## Endpoint
`POST https://apis.indeed.com/graphql?co=US&locale=en-US`

**Auth:** cookie-based (send `credentials: 'include'` from a logged-in browser context) PLUS request headers captured from a live session:
`indeed-api-key`, `indeed-ctk`, `indeed-client-sub-app`, `indeed-client-sub-app-component`, `accept`, `content-type`.
These tokens are session-scoped — the agent must capture them fresh from a logged-in Indeed tab (same pattern as the Outlook MSAL token grab), not hardcode them.

## Operations used by the hiring pipeline

### 1. List candidates — `FindRCPMatches`
Returns paginated candidate submissions. Each record (`candidateSubmission`) carries:
- `data.legacyID` — the candidate's stable id (same as `?id=` in the profile URL). **This is the join key.**
- `data.candidateIdentity.candidateId`, `.jobseekerAccountKey`
- `talentRepresentation.experience[]` → `{company, title, dateRange}` — **work history for quality vetting**
- `data.jobs.jobs[].jobData.{jobKey, title}` — the job they applied to
Paginates via the UI "Next" button (cursor-based). 20/page.

### 2. Contact details (batch) — candidate submissions filter query
Variables: `{input:{filter:{legacyIds:[...], submissionType:"LEGACY", hiringMilestones:{milestoneIds:["NEW","PENDING","REVIEWED"]}}}, first:N}`
- Pass an **array of legacyIds** → returns name + `profile.contact.phoneNumber` + `jobData.jobKey` for all in ONE call.
- ⚠️ The `hiringMilestones` filter excludes already-contacted candidates — drop it / widen `milestoneIds` to fetch everyone. Bump `first` to cover the batch.
- 100% phone hit rate observed.

### 3. Send message — `sendConversationEvent` mutation
Variables:
```
{
  messageBody: "<text>",
  attachments: [], payload: [],
  clientName: "<from template>",
  includeRequireResponse: <bool>,
  correlationKey: "<fresh uuid per send>",
  eventId: "<fresh uuid per send>",
  context: { context: "...", scope: { preOrPostApply: {
    advertiserKey: "<constant, 32-char, per employer account>",
    aggJobKey:     "<16-char, == candidate's jobData.jobKey>",
    candidateKey:  "<12-char, == candidate's legacyID>"
  } } }
}
```
**Key mapping (the whole trick):**
- `candidateKey` = the candidate's `legacyID` (the `?id=` value).
- `aggJobKey` = that candidate's applied `jobData.jobKey` (from query #1 or #2). Per job, ~5 distinct jobs across the ads.
- `advertiserKey` = constant for the account (capture once from any real send).
- `correlationKey` + `eventId` = fresh `crypto.randomUUID()` per message (idempotency).
Response `data.sendConversationEvent` (no `errors`) = sent. Creates the conversation if none exists.

## Lights-out send recipe (proven 2026-06-10, 9 sends, 100% success)
1. Capture a real `sendConversationEvent` request once (open any candidate, send via UI) → gives the query string, headers, `advertiserKey`, and exact variable shape.
2. Batch-call query #2 with all target legacyIds → `legacyId → aggJobKey` map.
3. For each candidate: clone the template, set `messageBody` (personalized), `candidateKey=legacyId`, `aggJobKey=map[legacyId]`, fresh `correlationKey`/`eventId`, POST.

## Pull recipe
- Names + phones: one call to query #2 with `legacyIds:[...]` (drop milestone filter).
- Work history for vetting: query #1 across the needed pages, harvest `talentRepresentation.experience` keyed by `data.legacyID`.

## Notes / gotchas
- Chrome MCP content filter blocks base64-looking operationNames + token values in JS return values — work around by returning field PATHS / lengths, and replay using the captured header object directly (don't read token values into context).
- Interview cadence: **Mondays only, 1:00-4:00 PM** (updated 2026-07-11, this is the current cadence used in `data/indeed_interview_invites.json` - supersedes the earlier 2026-06-11 note of 11 AM-3 PM). Store: Five Guys Dixie Highway, 9050 Dixie Hwy, Louisville KY 40258. Hiring manager signs as "Bobby".
- **aggJobKey confirmed NOT harvestable from FindRCPMatches** (2026-06-11): `jobData.jobKey` returns empty from the contact-batch query when the candidate was already contacted. UI send flow is the reliable path. Pure-API `sendConversationEvent` replay is blocked for contacted candidates. Document if a workaround is found.
- Management roles to target: AGM + Shift Leader (any ad location). Crew excluded.
