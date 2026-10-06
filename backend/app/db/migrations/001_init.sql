-- Appeal Architect — migration 001: initial schema
--
-- This is health data. The rules it enforces:
--
--   * RLS is ON for every table, with no exceptions, scoped to auth.uid()
--     through cases.user_id. The backend uses the service-role key and so
--     bypasses RLS -- it derives user_id from the verified JWT and scopes every
--     query itself. RLS is the second line of defence for anything that reaches
--     Postgres by another path, which is exactly when you want it.
--   * Storage buckets are private. Documents are reached only through
--     short-lived signed URLs.
--   * Deleting a user deletes their rows. ON DELETE CASCADE throughout, so
--     DELETE /me/data is a real delete and not a soft flag.
--   * No PHI in llm_calls. Prompt hash only, never prompt content.
--
-- Apply with:
--   supabase db push
-- or:
--   psql "$DATABASE_URL" -f app/db/migrations/001_init.sql

begin;

-- ──────────────────────────────────────────────────────────────────────────────
-- Enumerated vocabulary
--
-- These values are a wire contract shared with app/domain/case.py and the
-- frontend's generated types. Changing a label is a migration, not a rename.
-- ──────────────────────────────────────────────────────────────────────────────

create type plan_type as enum (
  'aca_marketplace',
  'employer_fully_insured',
  'employer_self_funded',
  'medicare_advantage',
  'medicaid',
  'unknown'
);

create type service_timing as enum ('pre', 'post', 'concurrent');

create type case_stage as enum (
  'uploaded', 'extracted', 'confirmed', 'routed', 'arguing',
  'evidence', 'letter_ready', 'sent', 'responded', 'escalated', 'resolved'
);

create type document_kind as enum (
  'denial_letter', 'eob', 'plan_doc', 'medical_record', 'physician_letter', 'other'
);

-- The confirmation gate. Only 'confirmed' and 'edited' may reach the engine.
create type fact_status as enum ('pending', 'confirmed', 'edited', 'rejected');

create type evidence_status as enum ('missing', 'requested', 'have', 'optional');

-- ──────────────────────────────────────────────────────────────────────────────
-- Helpers
-- ──────────────────────────────────────────────────────────────────────────────

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ──────────────────────────────────────────────────────────────────────────────
-- profiles
-- ──────────────────────────────────────────────────────────────────────────────

create table profiles (
  user_id            uuid primary key references auth.users(id) on delete cascade,
  display_name       text,
  state              char(2),
  plan_tier          text not null default 'free',
  stripe_customer_id text,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create trigger profiles_updated_at
  before update on profiles
  for each row execute function set_updated_at();

-- ──────────────────────────────────────────────────────────────────────────────
-- cases
-- ──────────────────────────────────────────────────────────────────────────────

create table cases (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references auth.users(id) on delete cascade,
  title             text not null,
  insurer_name      text,
  claim_number      text,
  stage             case_stage not null default 'uploaded',
  plan_type         plan_type not null default 'unknown',
  state             char(2),
  denial_date       date,
  denial_received_date date,
  service_date      date,
  service_timing    service_timing,
  claim_amount_usd  numeric(12, 2),
  -- The user's own declaration that delay threatens their health. Drives the
  -- expedited track, so a determination relying on it carries a warning saying so.
  is_urgent_medical boolean not null default false,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index cases_user_id_idx on cases (user_id, created_at desc);

create trigger cases_updated_at
  before update on cases
  for each row execute function set_updated_at();

-- Used by every child table's RLS policy. SECURITY DEFINER with a pinned
-- search_path so a policy cannot be subverted by a shadowed table name.
create or replace function owns_case(target_case_id uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from public.cases c
    where c.id = target_case_id and c.user_id = auth.uid()
  );
$$;

-- ──────────────────────────────────────────────────────────────────────────────
-- documents
--
-- extracted_text is stored alongside the file so source spans can be
-- highlighted against the exact characters the model read. It is PHI: it lives
-- under RLS, and it is never logged.
-- ──────────────────────────────────────────────────────────────────────────────

create table documents (
  id             uuid primary key default gen_random_uuid(),
  case_id        uuid not null references cases(id) on delete cascade,
  kind           document_kind not null default 'other',
  storage_path   text not null,
  filename       text not null,
  mime           text not null,
  page_count     int,
  extracted_text text,
  ocr_used       boolean not null default false,
  uploaded_at    timestamptz not null default now()
);

create index documents_case_id_idx on documents (case_id);

-- ──────────────────────────────────────────────────────────────────────────────
-- extracted_facts
--
-- The LLM's proposals. A row is a proposal until status becomes 'confirmed' or
-- 'edited', and there is no code path from 'pending' to a conclusion.
-- source_start/source_end are character offsets into documents.extracted_text.
-- ──────────────────────────────────────────────────────────────────────────────

create table extracted_facts (
  id           uuid primary key default gen_random_uuid(),
  case_id      uuid not null references cases(id) on delete cascade,
  document_id  uuid references documents(id) on delete cascade,
  field        text not null,
  value        jsonb not null,
  confidence   real not null check (confidence >= 0 and confidence <= 1),
  source_page  int check (source_page >= 1),
  source_start int check (source_start >= 0),
  source_end   int check (source_end >= 0),
  status       fact_status not null default 'pending',
  confirmed_at timestamptz,
  edited_value jsonb,
  created_at   timestamptz not null default now(),

  constraint span_is_forwards check (
    source_start is null or source_end is null or source_end >= source_start
  ),
  -- A confirmed fact must record when it was confirmed: the audit trail for the
  -- gate is the gate.
  constraint confirmed_has_timestamp check (
    status not in ('confirmed', 'edited') or confirmed_at is not null
  ),
  -- An edited fact must carry the user's correction, or 'edited' means nothing.
  constraint edited_has_value check (
    status <> 'edited' or edited_value is not null
  )
);

create index extracted_facts_case_id_idx on extracted_facts (case_id, status);

-- ──────────────────────────────────────────────────────────────────────────────
-- route_determinations
--
-- Idempotent per (case_id, facts_hash, rulebase_version): recomputing a route
-- from identical facts under identical rules returns the stored determination
-- instead of re-running the solver.
-- ──────────────────────────────────────────────────────────────────────────────

create table route_determinations (
  id               uuid primary key default gen_random_uuid(),
  case_id          uuid not null references cases(id) on delete cascade,
  rulebase_version text not null,
  facts_hash       text not null,
  plan_type        plan_type not null,
  steps            jsonb not null default '[]'::jsonb,
  deadlines        jsonb not null default '[]'::jsonb,
  trace            jsonb not null default '[]'::jsonb,
  warnings         jsonb not null default '[]'::jsonb,
  computed_at      timestamptz not null default now(),

  unique (case_id, facts_hash, rulebase_version)
);

create index route_determinations_case_id_idx on route_determinations (case_id, computed_at desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- argument_graphs
-- ──────────────────────────────────────────────────────────────────────────────

create table argument_graphs (
  id              uuid primary key default gen_random_uuid(),
  case_id         uuid not null references cases(id) on delete cascade,
  schemes_version text not null,
  arguments       jsonb not null default '[]'::jsonb,
  attacks         jsonb not null default '[]'::jsonb,
  grounded        jsonb not null default '[]'::jsonb,
  preferred       jsonb not null default '[]'::jsonb,
  stable          jsonb not null default '[]'::jsonb,
  worth_adding    jsonb not null default '[]'::jsonb,
  defeated        jsonb not null default '[]'::jsonb,
  trace           jsonb not null default '[]'::jsonb,
  computed_at     timestamptz not null default now()
);

create index argument_graphs_case_id_idx on argument_graphs (case_id, computed_at desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- evidence_items
-- ──────────────────────────────────────────────────────────────────────────────

create table evidence_items (
  id                uuid primary key default gen_random_uuid(),
  case_id           uuid not null references cases(id) on delete cascade,
  key               text not null,
  label             text not null,
  why_needed        text,
  argument_node_ids jsonb not null default '[]'::jsonb,
  status            evidence_status not null default 'missing',
  document_id       uuid references documents(id) on delete set null,
  updated_at        timestamptz not null default now(),

  unique (case_id, key)
);

create trigger evidence_items_updated_at
  before update on evidence_items
  for each row execute function set_updated_at();

-- ──────────────────────────────────────────────────────────────────────────────
-- deadlines
--
-- Computed by the rules engine and stored, never recomputed in the browser.
-- ambiguous carries the engine's disclosure that the regulation's trigger was
-- unclear; ambiguity_note must be present when it is true, mirroring the check
-- in app/domain/route.py.
-- ──────────────────────────────────────────────────────────────────────────────

create table deadlines (
  id              uuid primary key default gen_random_uuid(),
  case_id         uuid not null references cases(id) on delete cascade,
  item_id         text not null,
  label           text not null,
  due_date        date not null,
  trigger_date    date not null,
  rule_id         text not null,
  citation        jsonb not null,
  ambiguous       boolean not null default false,
  ambiguity_note  text,
  acknowledged_at timestamptz,
  created_at      timestamptz not null default now(),

  unique (case_id, item_id),
  constraint ambiguous_is_explained check (
    not ambiguous or (ambiguity_note is not null and length(ambiguity_note) > 0)
  )
);

-- Drives the reminder job's lookup: deadlines due within N days, not yet passed.
create index deadlines_due_date_idx on deadlines (due_date) where acknowledged_at is null;
create index deadlines_case_id_idx on deadlines (case_id, due_date);

-- ──────────────────────────────────────────────────────────────────────────────
-- reminders_sent
--
-- The idempotency record for POST /internal/run-reminders. The unique
-- constraint is what makes running the job twice in one day harmless -- which
-- matters, because a cron that double-fires must not email someone twice about
-- the same deadline.
-- ──────────────────────────────────────────────────────────────────────────────

create table reminders_sent (
  id          uuid primary key default gen_random_uuid(),
  deadline_id uuid not null references deadlines(id) on delete cascade,
  days_before int not null,
  sent_at     timestamptz not null default now(),

  unique (deadline_id, days_before)
);

-- ──────────────────────────────────────────────────────────────────────────────
-- letters
-- ──────────────────────────────────────────────────────────────────────────────

create table letters (
  id                 uuid primary key default gen_random_uuid(),
  case_id            uuid not null references cases(id) on delete cascade,
  argument_graph_id  uuid references argument_graphs(id) on delete set null,
  version            int not null default 1,
  -- Paragraphs, each tagged with its argument_node_id or the reserved
  -- 'procedural' marker. Checked after generation; untagged LLM prose is dropped.
  body               jsonb not null default '[]'::jsonb,
  storage_path_pdf   text,
  storage_path_docx  text,
  generated_at       timestamptz not null default now(),

  unique (case_id, version)
);

create index letters_case_id_idx on letters (case_id, version desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- case_events — the record the user may need later
-- ──────────────────────────────────────────────────────────────────────────────

create table case_events (
  id         uuid primary key default gen_random_uuid(),
  case_id    uuid not null references cases(id) on delete cascade,
  kind       text not null,
  detail     jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index case_events_case_id_idx on case_events (case_id, created_at desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- rulebase_versions — which rules were in force, and what they were based on
-- ──────────────────────────────────────────────────────────────────────────────

create table rulebase_versions (
  version     text primary key,
  released_at timestamptz not null default now(),
  changelog   text,
  sources     jsonb not null default '[]'::jsonb,
  is_current  boolean not null default false
);

-- Only one version may be current at a time.
create unique index rulebase_versions_one_current_idx
  on rulebase_versions (is_current) where is_current;

-- ──────────────────────────────────────────────────────────────────────────────
-- llm_calls — NO PHI
--
-- Prompt hash only, never prompt content. No case_id column, deliberately:
-- linking a call to a case is a step towards linking it to a diagnosis. This is
-- enough to enforce the per-user monthly cap and to see what the LLM cost,
-- which is all it is for.
-- ──────────────────────────────────────────────────────────────────────────────

create table llm_calls (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  purpose       text not null,
  model         text not null,
  prompt_hash   text not null,
  input_tokens  int,
  output_tokens int,
  latency_ms    int,
  created_at    timestamptz not null default now()
);

create index llm_calls_user_month_idx on llm_calls (user_id, created_at desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- public_triage_hits — rate limiting without Redis
--
-- POST /public/triage is unauthenticated, so it needs a limit. A Postgres
-- counter survives Render's restarts, where an in-process bucket does not, and
-- the free tier is single-instance so there is no distributed-counter problem.
--
-- ip_hash is a salted hash. The raw IP is never stored.
-- ──────────────────────────────────────────────────────────────────────────────

create table public_triage_hits (
  id         bigserial primary key,
  ip_hash    text not null,
  created_at timestamptz not null default now()
);

create index public_triage_hits_lookup_idx on public_triage_hits (ip_hash, created_at desc);

-- ──────────────────────────────────────────────────────────────────────────────
-- Row Level Security — on every table, no exceptions
-- ──────────────────────────────────────────────────────────────────────────────

alter table profiles             enable row level security;
alter table cases                enable row level security;
alter table documents            enable row level security;
alter table extracted_facts      enable row level security;
alter table route_determinations enable row level security;
alter table argument_graphs      enable row level security;
alter table evidence_items       enable row level security;
alter table deadlines            enable row level security;
alter table reminders_sent       enable row level security;
alter table letters              enable row level security;
alter table case_events          enable row level security;
alter table rulebase_versions    enable row level security;
alter table llm_calls            enable row level security;
alter table public_triage_hits   enable row level security;

-- profiles: your own row.
create policy profiles_own on profiles
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- cases: your own cases.
create policy cases_own on cases
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());

-- Everything hanging off a case: reachable only if you own the case.
create policy documents_own on documents
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy extracted_facts_own on extracted_facts
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy route_determinations_own on route_determinations
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy argument_graphs_own on argument_graphs
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy evidence_items_own on evidence_items
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy deadlines_own on deadlines
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy letters_own on letters
  for all using (owns_case(case_id)) with check (owns_case(case_id));

create policy case_events_own on case_events
  for all using (owns_case(case_id)) with check (owns_case(case_id));

-- reminders_sent: reachable through the deadline's case.
create policy reminders_sent_own on reminders_sent
  for all using (
    exists (
      select 1 from deadlines d
      where d.id = reminders_sent.deadline_id and owns_case(d.case_id)
    )
  );

-- llm_calls: your own usage. Read-only to the client; only the backend writes.
create policy llm_calls_own_read on llm_calls
  for select using (user_id = auth.uid());

-- rulebase_versions: public reference data. Readable by anyone signed in,
-- writable only by the backend's service role.
create policy rulebase_versions_read on rulebase_versions
  for select using (true);

-- public_triage_hits: no client access at all. The service role bypasses RLS,
-- so leaving this with no permissive policy denies every other caller.

-- ──────────────────────────────────────────────────────────────────────────────
-- Storage — private buckets, signed URLs only
-- ──────────────────────────────────────────────────────────────────────────────

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false), ('letters', 'letters', false)
on conflict (id) do nothing;

-- Objects are laid out as {case_id}/{filename}, so the first path segment is the
-- case and ownership follows from it.
create policy documents_bucket_own on storage.objects
  for all using (
    bucket_id = 'documents'
    and owns_case(nullif(split_part(name, '/', 1), '')::uuid)
  );

create policy letters_bucket_own on storage.objects
  for all using (
    bucket_id = 'letters'
    and owns_case(nullif(split_part(name, '/', 1), '')::uuid)
  );

-- ──────────────────────────────────────────────────────────────────────────────
-- Seed: the rulebase version this migration ships with
-- ──────────────────────────────────────────────────────────────────────────────

insert into rulebase_versions (version, changelog, sources, is_current)
values (
  '1.0.0',
  'Seed tables only; no .lp rules yet. Every value is UNVERIFIED. See backend/app/rules/rulebase/CHANGELOG.md.',
  '["45 CFR 147.136 (unverified)", "29 CFR 2560.503-1 (unverified)"]'::jsonb,
  true
)
on conflict (version) do nothing;

commit;
