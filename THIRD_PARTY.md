# Third-party accounts and keys

Five services. Everything on a free tier except Anthropic and Stripe, which are
pay-as-you-go.

Fill these into two files, both of which `.gitignore` already covers:

- `backend/.env` — copy from `.env.example`, backend block
- `frontend/.env.local` — copy from `.env.example`, frontend block

```bash
cp .env.example backend/.env
cp .env.example frontend/.env.local
```

## What you need, in the order you need it

| # | Service | What for | Needed by | Cost |
|---|---|---|---|---|
| 1 | **Supabase** | database, sign-in, document storage | signing in at all | free tier |
| 2 | **Anthropic** | reading documents, writing letter prose | uploading a letter | pay per use |
| 3 | **Resend** | sign-in links, deadline reminders | reminders working | free: 3,000/mo |
| 4 | **Stripe** | the Appeal Package and the subscription | taking money | 1.5% + 20p |
| 5 | **Render + Cloudflare** | hosting | going live | free tiers |

You can run the whole app locally with only **1 and 2**. Without any of them it
still starts, and `GET /healthz` tells you which are missing rather than
crashing.

---

## 1. Supabase — database, auth, file storage

**Free tier.** Pauses after ~7 days of no database traffic; resume it from the
dashboard and nothing is lost.

### Get it

1. <https://supabase.com/dashboard> → **New project**. Pick a region near your
   users. Save the database password it shows you — it is shown once.
2. **SQL Editor** → paste and run each migration in order:
   - `backend/app/db/migrations/001_init.sql`
   - `backend/app/db/migrations/002_case_fields.sql`
   - `backend/app/db/migrations/003_billing_and_profiles.sql`
3. **Authentication → Providers → Email**: enable it, and enable **Magic Link**.
   There are no passwords in this product.
4. **Authentication → URL Configuration**:
   - Site URL: `http://localhost:3000` (your real domain later)
   - Redirect URLs: add `http://localhost:3000/auth/callback/`
   - **The trailing slash matters.** The frontend is a static export with
     `trailingSlash: true`, so `/auth/callback` without it will 404.
5. **Project Settings → API** — four values:

| Dashboard field | Variable | Goes in |
|---|---|---|
| Project URL | `SUPABASE_URL` | `backend/.env` |
| Project URL | `NEXT_PUBLIC_SUPABASE_URL` | `frontend/.env.local` |
| `anon` `public` key | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `frontend/.env.local` |
| `service_role` `secret` key | `SUPABASE_SERVICE_ROLE_KEY` | `backend/.env` |
| JWT Settings → JWT Secret | `SUPABASE_JWT_SECRET` | `backend/.env` |

> ⚠️ **The `service_role` key bypasses every row-level security policy.** It
> belongs in `backend/.env` and nowhere else. It must never appear in a
> `NEXT_PUBLIC_*` variable, because everything with that prefix is compiled into
> the static bundle and served to every visitor. The `anon` key in the frontend is
> safe and is meant to be public — RLS is what protects the data.

### Check it

```bash
curl localhost:8000/healthz    # "supabase": true
```

Then sign up through the app and land on an empty case list. To prove RLS is
doing its job, sign up as a second account and confirm you see none of the first
account's cases.

---

## 2. Anthropic — reading documents and writing prose

**Pay as you go.** This is the only per-use cost in the product.

### Get it

1. <https://console.anthropic.com> → sign up.
2. **Billing** → add a payment method and a small amount of credit. Start with
   $20; that is a lot of denial letters.
3. **API Keys** → **Create key**. Copy it immediately — it is shown once.

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
LLM_MONTHLY_CALL_CAP=200
```

### What it costs you per case

Claude Sonnet 4.6 is $3 per million input tokens and $15 per million output.

| Job | Rough tokens | Rough cost |
|---|---|---|
| Transcribing a scanned page (per page) | 2k in, 1.5k out | ~$0.03 |
| Reading a letter and proposing facts | 4k in, 1k out | ~$0.03 |
| Writing the letter paragraphs | 3k in, 2k out | ~$0.04 |
| **A typical 3-page case, end to end** | | **~$0.15** |

At a £39 Appeal Package that is a rounding error. `LLM_MONTHLY_CALL_CAP` is the
per-user ceiling, checked **before** each call, so a runaway cannot happen.

### Worth knowing

- **No training on your users' data.** Anthropic does not train on API inputs or
  outputs. Confirm this against the commercial terms in force when you launch,
  and note the date in `docs/DEPLOY.md` — `docs/PRIVACY.md` makes this claim to
  your users on your behalf.
- `claude-sonnet-4-6` is the model the build specifies and what the extraction
  path is written against. `claude-sonnet-5-5` is newer and cheaper ($2/$10) but
  rejects forced tool use and `temperature`, so switching it needs the extraction
  call rewritten, not just the variable changed. Worth doing once you have usage
  to measure; see `PLAN.md` §4.7.
- There is no fallback if this key is missing. Document upload returns a 503
  naming the variable. The rules engine and everything about deadlines works
  without it, because the engine does not use a model at all.

---

## 3. Resend — email

**Free tier: 3,000 emails a month, 100 a day.** Plenty.

### Get it

1. <https://resend.com> → sign up.
2. **Domains** → **Add domain** → add the DNS records it gives you (SPF, DKIM,
   and a return-path CNAME) at your registrar. Verification usually takes
   minutes.
3. **API Keys** → **Create API Key**, sending permission only.

```
RESEND_API_KEY=re_...
FROM_EMAIL=deadlines@yourdomain.com
```

### Do not skip the domain

You can test against Resend's sandbox domain, but deadline reminders sent from an
unverified domain land in spam — and a spam-foldered deadline reminder is the
exact failure this product exists to prevent. Verify the domain before launch.

Use a sending address people will recognise, like `deadlines@`. These emails
carry the deadline and the case name and no clinical detail at all, because they
may be read on a shared screen.

---

## 4. Stripe — payment

Only needed when you want to charge. Everything else works without it.

### Get it

1. <https://dashboard.stripe.com> → sign up. **Stay in test mode** while you are
   building; the keys are separate.
2. **Products** → create two:
   - **Appeal Package** — one-time price (the UI says £39)
   - **Subscription** — recurring monthly price (the UI says £12)
   Copy each one's **price ID** (`price_...`), not the product ID.
3. **Developers → API keys** → copy the **Secret key**.
4. **Developers → Webhooks** → **Add endpoint**:
   - URL: `https://your-api.onrender.com/api/v1/billing/webhook`
   - Events: `checkout.session.completed`,
     `customer.subscription.deleted`, `customer.subscription.paused`
   - Copy the **Signing secret** (`whsec_...`)

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_APPEAL_PACKAGE=price_...
STRIPE_PRICE_SUBSCRIPTION=price_...
```

### Testing it locally

```bash
stripe listen --forward-to localhost:8000/api/v1/billing/webhook
```

That prints a different `whsec_` for the local session — use that one while
testing.

### What the webhook controls

It sets `profiles.plan_tier`, which is the only thing gating letter generation.
The route, the deadlines, the rule behind each one and the reminder emails are
**never** gated, and a cancelled subscription drops to free without touching
cases, deadlines or letters already generated. Nothing in Stripe ever receives a
case id, a diagnosis or anything clinical.

---

## 5. Hosting — Render and Cloudflare Pages

### Backend → Render

**Free tier.** Sleeps after 15 minutes idle; the frontend shows a warming state
on the first call rather than an error.

1. <https://render.com> → **New** → **Blueprint**, pointed at this repo.
   `render.yaml` declares both services.
2. Set every `sync: false` variable in the Render dashboard. `INTERNAL_JOB_SECRET`
   is generated for you.
3. Set `CORS_ORIGINS` to your Cloudflare Pages domain.

### Frontend → Cloudflare Pages

1. <https://dash.cloudflare.com> → **Workers & Pages** → **Create** → connect the
   repo.
2. Framework preset: **Next.js (Static HTML Export)**
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `out`
3. Environment variables: the three `NEXT_PUBLIC_*` values.
   `NEXT_PUBLIC_API_URL` is your Render URL.
4. Back in Supabase, add the Pages domain to **Redirect URLs** as
   `https://yourdomain.com/auth/callback/`.

> `NEXT_PUBLIC_*` variables are baked in **at build time**, not read at runtime.
> Change one and you must redeploy the frontend for it to take effect.

### ⚠️ The reminder cron — the one step whose omission is invisible

`render.yaml` declares it, so a Blueprint deploy sets it up. Verify it ran.

If you deploy by hand instead, set it up yourself — and understand what happens
if you forget. There is no error, no failed request and no alert. Deadline
reminder emails simply never arrive, and a user who was relying on them misses
their filing window.

```bash
# Confirm it works. Safe to run twice: the endpoint is idempotent.
curl -X POST -H "X-Internal-Job-Secret: $INTERNAL_JOB_SECRET" \
  https://your-api.onrender.com/api/v1/internal/run-reminders
```

A second run reports everything as already sent and writes nothing, because
`reminders_sent` is unique on `(deadline_id, days_before)`. That is also how you
check the wiring without emailing anyone twice.

### Also worth setting up

- **An uptime monitor** on `https://your-api.onrender.com/healthz`
  (<https://betteruptime.com> or <https://uptimerobot.com>, both free) to keep the
  Render service awake. Note it does **not** keep the Supabase database awake —
  only database traffic does that.

---

## The complete environment, in one place

### `backend/.env`

```bash
# Supabase — required for anything to work
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...          # server only, bypasses RLS
SUPABASE_JWT_SECRET=your-jwt-secret

# Anthropic — required to read documents
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6
LLM_MONTHLY_CALL_CAP=200

# Resend — required for reminders
RESEND_API_KEY=re_...
FROM_EMAIL=deadlines@yourdomain.com

# Stripe — required to charge
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_APPEAL_PACKAGE=price_...
STRIPE_PRICE_SUBSCRIPTION=price_...

# Generate with: openssl rand -hex 32
INTERNAL_JOB_SECRET=

CORS_ORIGINS=http://localhost:3000
RULEBASE_VERSION=1.0.0
SCHEMES_VERSION=1.0.0
ENV=development

# Cron service only
API_BASE_URL=http://localhost:8000
```

### `frontend/.env.local`

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...       # public by design
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Before you launch

- [ ] All three migrations applied
- [ ] RLS proven: a second account sees none of the first account's cases
- [ ] `ENV=production` on Render — this also stops `/docs` being served
- [ ] `CORS_ORIGINS` is your real domain, not `localhost`
- [ ] `service_role` key is **not** in any `NEXT_PUBLIC_*` variable
- [ ] Resend domain verified, and a test reminder lands in an inbox not spam
- [ ] **Reminder cron configured, and seen to fire**
- [ ] Uptime monitor pinging `/healthz`
- [ ] Stripe webhook receiving events (check Developers → Webhooks → attempts)
- [ ] Delete-my-data run end to end on a throwaway account, and nothing left
- [ ] Anthropic's no-training terms confirmed, with the date noted in
      `docs/DEPLOY.md`
- [ ] **Every `UNVERIFIED` legal value either verified or still visibly flagged
      in the UI** — see `docs/RULEBASE.md`. This one is not optional: the dates
      this product shows are the dates people will act on.
