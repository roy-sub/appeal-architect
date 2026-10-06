# Migrations

Numbered, forward-only plain SQL. No Alembic: Supabase owns the schema, and the
spec's stack does not include a Python migration tool.

Apply in order. Each file is idempotent at the statement level where it can be
(`on conflict do nothing`, `create or replace`) but the files themselves are not
re-runnable — `create type` will fail on a second run. Apply each one once.

```bash
# via the Supabase CLI, from backend/
supabase db push

# or directly
psql "$DATABASE_URL" -f app/db/migrations/001_init.sql
```

| File | What it does |
|---|---|
| `001_init.sql` | Enums, all 14 tables, RLS on every one, the two private storage buckets, and the seed `rulebase_versions` row |

## Things to know before changing the schema

- **RLS is on for every table.** The backend uses the service-role key and
  therefore bypasses it, so every backend query must scope by user explicitly.
  RLS catches anything that reaches Postgres by another path.
- **`on delete cascade` throughout** is what makes `DELETE /me/data` a real
  delete rather than a soft flag.
- **`llm_calls` has no `case_id`.** That is deliberate: linking an LLM call to a
  case is a step towards linking it to a diagnosis.
- **Enum labels are a wire contract** shared with `app/domain/case.py` and the
  frontend's types. Changing a label is a migration, not a rename.
