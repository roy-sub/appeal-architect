"""Migration 001 applies, its constraints bite, and RLS isolates users.

This is the test behind the claim "RLS verified by a second user seeing zero
rows". It applies the real migration to a real Postgres and then tries to read
one user's PHI as another user.

It needs a Postgres. Set ``TEST_DATABASE_URL`` to a database the test may
**drop and recreate** -- it is destructive by design, because a migration test
against a dirty schema proves nothing. Skipped when the variable is unset, so
``pytest`` stays green on a clone with no database.

    createdb aa_test
    TEST_DATABASE_URL=postgresql://localhost/aa_test pytest tests/test_migration_rls.py

``tests/fixtures/supabase_stub.sql`` stands in for the Supabase-managed ``auth``
and ``storage`` schemas, including an ``auth.uid()`` that reads
``request.jwt.claim.sub`` the way Supabase's does.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

DB_URL = os.environ.get("TEST_DATABASE_URL")
MIGRATION = Path(__file__).resolve().parent.parent / "app" / "db" / "migrations" / "001_init.sql"
STUB = Path(__file__).resolve().parent / "fixtures" / "supabase_stub.sql"

pytestmark = [
    pytest.mark.skipif(not DB_URL, reason="set TEST_DATABASE_URL to run migration tests"),
    pytest.mark.skipif(not shutil.which("psql"), reason="psql not on PATH"),
]

ALEX = "aaaa0000-0000-0000-0000-00000000000a"
BLAKE = "bbbb0000-0000-0000-0000-00000000000b"
ALEX_CASE = "11110000-0000-0000-0000-000000000001"
BLAKE_CASE = "22220000-0000-0000-0000-000000000002"


def _psql(sql: str, *, stop_on_error: bool = True) -> subprocess.CompletedProcess[str]:
    args = ["psql", DB_URL, "-X", "-q", "-A", "-t", "--no-psqlrc"]
    if stop_on_error:
        args += ["-v", "ON_ERROR_STOP=1"]
    return subprocess.run(args, input=sql, capture_output=True, text=True, check=False)


def _psql_file(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["psql", DB_URL, "-X", "-q", "--no-psqlrc", "-v", "ON_ERROR_STOP=1", "-f", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def schema() -> None:
    """Drop everything, apply the stub, apply migration 001."""
    wipe = _psql(
        """
        drop schema if exists public cascade;
        drop schema if exists auth cascade;
        drop schema if exists storage cascade;
        create schema public;
        """
    )
    assert wipe.returncode == 0, wipe.stderr

    stub = _psql_file(STUB)
    assert stub.returncode == 0, stub.stderr

    applied = _psql_file(MIGRATION)
    assert applied.returncode == 0, f"migration 001 failed to apply:\n{applied.stderr}"


@pytest.fixture
def seeded(schema: None) -> None:
    """Two users, a case each, a document each with distinguishable text."""
    result = _psql(
        f"""
        set role none;
        delete from auth.users;
        insert into auth.users (id, email)
          values ('{ALEX}', 'alex@example.com'), ('{BLAKE}', 'blake@example.com');
        insert into cases (id, user_id, title)
          values ('{ALEX_CASE}', '{ALEX}', 'Alex case'),
                 ('{BLAKE_CASE}', '{BLAKE}', 'Blake case');
        insert into documents (case_id, storage_path, filename, mime, extracted_text)
          values ('{ALEX_CASE}', 'a/1.pdf', 'denial.pdf', 'application/pdf', 'ALEX_PHI'),
                 ('{BLAKE_CASE}', 'b/1.pdf', 'denial.pdf', 'application/pdf', 'BLAKE_PHI');
        do $$ begin
          if not exists (select 1 from pg_roles where rolname = 'authenticated') then
            create role authenticated nologin;
          end if;
        end $$;
        grant usage on schema public, auth, storage to authenticated;
        grant select, insert, update, delete on all tables in schema public to authenticated;
        grant usage, select on all sequences in schema public to authenticated;
        grant select on auth.users to authenticated;
        """
    )
    assert result.returncode == 0, result.stderr


def _as(user_id: str | None, query: str, *, stop_on_error: bool = True):
    """Run a query as the unprivileged `authenticated` role with this JWT subject.

    RLS is bypassed by superusers and table owners, so testing as `postgres`
    would prove nothing at all.
    """
    claim = (
        f"set request.jwt.claim.sub = '{user_id}';" if user_id else "reset request.jwt.claim.sub;"
    )
    return _psql(f"set role authenticated; {claim} {query}", stop_on_error=stop_on_error)


# ---- the migration itself ---------------------------------------------------


def test_migration_applies_cleanly(schema: None) -> None:
    out = _psql(
        "select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = 'public' and c.relkind = 'r';"
    )
    assert out.returncode == 0, out.stderr
    assert int(out.stdout.strip()) == 14


def test_rls_is_enabled_on_every_public_table(schema: None) -> None:
    """Spec 9: RLS on every table. No exceptions, so the test allows none."""
    out = _psql(
        """
        select coalesce(string_agg(c.relname, ', ' order by c.relname), '')
        from pg_class c join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;
        """
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "", f"tables without RLS: {out.stdout.strip()}"


# ---- isolation --------------------------------------------------------------


def test_user_sees_only_their_own_cases(seeded: None) -> None:
    assert _as(ALEX, "select title from cases;").stdout.strip() == "Alex case"
    assert _as(BLAKE, "select title from cases;").stdout.strip() == "Blake case"


def test_user_cannot_read_another_users_phi(seeded: None) -> None:
    """The one that matters. Document text is the denial letter itself."""
    alex = _as(ALEX, "select extracted_text from documents;").stdout
    assert "ALEX_PHI" in alex
    assert "BLAKE_PHI" not in alex


def test_second_user_sees_zero_rows_of_the_first(seeded: None) -> None:
    out = _as(BLAKE, f"select count(*) from cases where id = '{ALEX_CASE}';")
    assert out.stdout.strip() == "0"


def test_user_cannot_write_into_another_users_case(seeded: None) -> None:
    """Read isolation without write isolation is not isolation."""
    out = _as(
        BLAKE,
        f"""insert into documents (case_id, storage_path, filename, mime)
            values ('{ALEX_CASE}', 'evil/1.pdf', 'x.pdf', 'application/pdf');""",
        stop_on_error=False,
    )
    assert "row-level security" in (out.stderr + out.stdout).lower()


def test_unauthenticated_sees_nothing(seeded: None) -> None:
    out = _as(None, "select count(*) from cases;")
    assert out.stdout.strip() == "0"


def test_rate_limit_table_is_opaque_to_clients(seeded: None) -> None:
    """``public_triage_hits`` has RLS on and no permissive policy.

    Only the service role, which bypasses RLS, may touch it.
    """
    out = _as(ALEX, "select count(*) from public_triage_hits;")
    assert out.stdout.strip() == "0"


# ---- constraints that encode product rules ---------------------------------


def test_confirmed_fact_must_record_when_it_was_confirmed(seeded: None) -> None:
    out = _psql(
        f"""set role none;
            insert into extracted_facts (case_id, field, value, confidence, status)
            values ('{ALEX_CASE}', 'denial_date', '"2026-09-14"', 0.9, 'confirmed');""",
        stop_on_error=False,
    )
    assert "confirmed_has_timestamp" in out.stderr


def test_edited_fact_must_carry_the_users_correction(seeded: None) -> None:
    out = _psql(
        f"""set role none;
            insert into extracted_facts (case_id, field, value, confidence, status, confirmed_at)
            values ('{ALEX_CASE}', 'denial_date', '"2026-09-14"', 0.9, 'edited', now());""",
        stop_on_error=False,
    )
    assert "edited_has_value" in out.stderr


def test_ambiguous_deadline_must_be_explained(seeded: None) -> None:
    """Mirrors the model-level check in app/domain/route.py.

    A conservative date stored without its explanation would reach the UI as a
    bare certainty.
    """
    out = _psql(
        f"""set role none;
            insert into deadlines (case_id, item_id, label, due_date, trigger_date,
                                   rule_id, citation, ambiguous)
            values ('{ALEX_CASE}', 'internal', 'File appeal', '2027-03-13', '2026-09-14',
                    'fed.x', '{{}}'::jsonb, true);""",
        stop_on_error=False,
    )
    assert "ambiguous_is_explained" in out.stderr


def test_reminder_cannot_be_sent_twice(seeded: None) -> None:
    """Spec 8: the reminder endpoint is idempotent when run twice.

    The unique constraint is what makes a double-firing cron harmless.
    """
    setup = _psql(
        f"""set role none;
            insert into deadlines (case_id, item_id, label, due_date,
                                   trigger_date, rule_id, citation)
            values ('{ALEX_CASE}', 'internal', 'File appeal', '2027-03-13', '2026-09-14',
                    'fed.x', '{{}}'::jsonb)
            on conflict do nothing;
            insert into reminders_sent (deadline_id, days_before)
            select id, 30 from deadlines where case_id = '{ALEX_CASE}' limit 1;"""
    )
    assert setup.returncode == 0, setup.stderr

    again = _psql(
        f"""set role none;
            insert into reminders_sent (deadline_id, days_before)
            select id, 30 from deadlines where case_id = '{ALEX_CASE}' limit 1;""",
        stop_on_error=False,
    )
    assert "duplicate key" in again.stderr


def test_only_one_rulebase_version_is_current(seeded: None) -> None:
    out = _psql(
        """set role none;
           insert into rulebase_versions (version, is_current) values ('9.9.9', true);""",
        stop_on_error=False,
    )
    assert "rulebase_versions_one_current_idx" in out.stderr


def test_deleting_a_user_leaves_nothing_behind(seeded: None) -> None:
    """DELETE /me/data is a real delete, and the cascade is what makes it one."""
    deleted = _psql(f"set role none; delete from auth.users where id = '{ALEX}';")
    assert deleted.returncode == 0, deleted.stderr

    remaining = _psql(
        f"""set role none;
            select (select count(*) from cases where user_id = '{ALEX}')
                 + (select count(*) from documents where case_id = '{ALEX_CASE}')
                 + (select count(*) from extracted_facts where case_id = '{ALEX_CASE}')
                 + (select count(*) from deadlines where case_id = '{ALEX_CASE}');"""
    )
    assert remaining.stdout.strip() == "0"
