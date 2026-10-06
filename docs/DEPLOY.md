# Deploy

Free tier throughout: Supabase free, Render free, Cloudflare Pages. No Redis, no
Celery, no always-on worker.

## Phase 1: what you need to do now

The rest of this file describes the phase 8 production deploy. **This section is
the part that is live today** — it closes the last item of the Phase 1 Definition
of Done, which needs a Supabase project that only you can create.

### 1. Create the Supabase project

1. <https://supabase.com/dashboard> → **New project**. Free tier.
2. Pick a region near you. Save the database password somewhere safe — it is
   shown once.

### 2. Apply migration 001

Either from the dashboard — **SQL Editor** → paste
`backend/app/db/migrations/001_init.sql` → **Run** — or from the CLI:

```bash
cd backend
supabase link --project-ref <your-project-ref>
supabase db push
```

It creates 14 tables, enables RLS on every one, and creates the two private
storage buckets.

### 3. Turn on magic-link sign-in

**Authentication → Providers → Email**: enable it, and enable **Magic Link**.

**Authentication → URL Configuration**:
- Site URL: `http://localhost:3000`
- Redirect URLs: add `http://localhost:3000/auth/callback/`

The trailing slash matters — the frontend is a static export with
`trailingSlash: true`, so `/auth/callback` without it will 404.

### 4. Copy four values into your environment

From **Project Settings → API**:

| Dashboard field | Goes to | Variable |
|---|---|---|
| Project URL | `backend/.env` | `SUPABASE_URL` |
| Project URL | `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_URL` |
| `anon` `public` key | `frontend/.env.local` | `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| `service_role` `secret` key | `backend/.env` | `SUPABASE_SERVICE_ROLE_KEY` |
| JWT Settings → JWT Secret | `backend/.env` | `SUPABASE_JWT_SECRET` |

```bash
cp .env.example backend/.env       # fill in the backend block
cp .env.example frontend/.env.local # fill in the frontend block
```

**The `service_role` key bypasses RLS.** It belongs in `backend/.env` only. It
must never appear in a `NEXT_PUBLIC_*` variable, because everything with that
prefix is compiled into the static bundle and served to every visitor.

### 5. Check it

```bash
curl localhost:8000/healthz   # "supabase": true
```

Then sign up through the app and land on an empty case list.

---

## Phase 8: production

> Not yet live. Recorded here so the checklist exists before it is needed.

### Backend → Render

- New **Web Service**, Docker, free plan, pointed at `backend/Dockerfile`.
- Environment: every variable in the backend block of `.env.example`, plus
  `ENV=production` and `CORS_ORIGINS` set to the Pages domain.
- The free service **sleeps after 15 minutes idle**. The frontend shows a warming
  state on the first call rather than an error, and an external uptime monitor
  pings `/healthz` to keep it awake.

### Frontend → Cloudflare Pages

- Build command `npm run build`, output directory `out`, root `frontend`.
- Environment: the three `NEXT_PUBLIC_*` variables. `NEXT_PUBLIC_API_URL` points
  at the Render service.
- Add the Pages domain to Supabase's redirect URLs and to the backend's
  `CORS_ORIGINS`.

### Database → Supabase

- The free tier **pauses after about 7 days of inactivity**. Resume it from the
  dashboard; nothing is lost, but the first request after a pause fails. The
  uptime monitor on `/healthz` does not keep the database awake — only database
  traffic does.

### ⚠️ The reminder cron — configure it or deadlines silently stop notifying

This is the one step whose omission is invisible until it has already harmed
someone. There is no error, no failed request, no alert: deadline reminder emails
simply never arrive, and a user who was relying on them misses their filing
window.

Set up **one** of these, and verify it fired:

**Supabase `pg_cron`:**

```sql
select cron.schedule(
  'appeal-architect-reminders',
  '0 13 * * *',  -- 13:00 UTC daily
  $$ select net.http_post(
       url     := 'https://<your-render-service>.onrender.com/internal/run-reminders',
       headers := '{"X-Internal-Job-Secret": "<INTERNAL_JOB_SECRET>"}'::jsonb
     ); $$
);
```

**Or a Render Cron Job**, daily:

```bash
curl -fsS -X POST \
  -H "X-Internal-Job-Secret: $INTERNAL_JOB_SECRET" \
  https://<your-render-service>.onrender.com/internal/run-reminders
```

The endpoint is idempotent — the `reminders_sent` unique constraint on
`(deadline_id, days_before)` means a double-firing cron cannot email the same
person twice about the same deadline. Running it twice by hand is a safe way to
check.

Note that Render's free web service sleeps: the first cron call of the day may
wake it and time out. Either keep it warm with the uptime monitor or have the
cron retry once.

### Stripe

- Products: one-time **Appeal Package**, and the subscription.
- Webhook endpoint `/api/v1/billing/webhook`, with the signing secret in
  `STRIPE_WEBHOOK_SECRET`.
- Test with Stripe's CLI against the deployed URL before going live.

### Pre-launch checklist

- [ ] Migration applied; RLS verified by signing in as a second account and
      seeing zero rows of the first
- [ ] `ENV=production` — `/docs` and `/openapi.json` are then not served
- [ ] `CORS_ORIGINS` is the real domain, not `localhost`
- [ ] Service-role key is **not** in any `NEXT_PUBLIC_*` variable
- [ ] **Reminder cron configured, and seen to fire**
- [ ] Uptime monitor pinging `/healthz`
- [ ] Hard delete verified end to end: delete an account, confirm nothing remains
      in any table or bucket
- [ ] PHI-free logging verified against a real request log
- [ ] Anthropic's no-training terms confirmed in the commercial terms then in
      force, and the date recorded here
- [ ] Every `UNVERIFIED` value either verified or still visibly flagged in the UI
- [ ] `rulebase_versions.is_current` matches `RULEBASE_VERSION`
