# Privacy and data flow

This product handles protected health information. A denial letter names a
person, their insurer, their claim, and the treatment they were refused — which
means it names their diagnosis. The medical records uploaded alongside it are
more sensitive still.

This document is the data-flow record required by the project's hard rules. It
describes what the system does, where PHI lives, and what it deliberately does
not do.

## What we hold

| Data | Where | Encrypted | Deleted by `DELETE /me/data` |
|---|---|---|---|
| Account email | Supabase Auth | at rest + in transit | yes |
| Case metadata (insurer, claim number, dates, amounts) | `cases` | at rest + in transit | yes |
| Uploaded documents (denial letter, EOB, plan docs, medical records) | Supabase Storage, private bucket | at rest + in transit | yes, objects and rows |
| Extracted document text | `documents.extracted_text` | at rest + in transit | yes |
| Proposed and confirmed facts | `extracted_facts` | at rest + in transit | yes |
| Route determinations, argument graphs, deadlines | `route_determinations`, `argument_graphs`, `deadlines` | at rest + in transit | yes |
| Generated letters | `letters` + Storage, private bucket | at rest + in transit | yes |
| Case timeline | `case_events` | at rest + in transit | yes |
| Reminder send log | `reminders_sent` | at rest + in transit | yes |
| LLM call metadata — **no PHI** | `llm_calls` | at rest + in transit | yes |
| Rate-limit counters — salted IP hash only | `public_triage_hits` | at rest + in transit | n/a (no user link) |

Encryption at rest is provided by Supabase Postgres and Supabase Storage.
Everything in transit is TLS: browser to API, API to Supabase, API to Anthropic,
API to the email provider.

## The flow, end to end

1. **Upload.** The file goes to a private Supabase Storage bucket under
   `{case_id}/{filename}`. The bucket is not public. The browser reaches a file
   only through a short-lived signed URL.
2. **Text extraction.** `pypdfium2` reads the PDF's text layer; a page with no
   text layer is rasterised and OCR'd with Tesseract. Per-page text is stored
   with character offsets preserved, so a proposed fact can be shown next to the
   exact characters it came from.
3. **LLM extraction.** The document text is sent to Anthropic's API to produce
   `ExtractedFact` proposals. **This is the one point where PHI leaves our
   infrastructure.** See the next section.
4. **Confirmation.** Each proposal is shown to the user beside its source span.
   Nothing proceeds until the required facts are confirmed or corrected.
5. **The engine.** Confirmed facts go to the rules engine and the argumentation
   solver, both of which run in-process with no network access at all. They
   cannot send data anywhere; the architecture test proves they have no import
   path to a network client.
6. **Letter.** Accepted argument nodes and confirmed facts go to the LLM to be
   rendered as prose. DOCX and PDF are generated server-side and stored in a
   private bucket.
7. **Reminders.** A daily scheduled job finds deadlines 30/14/7/3/1 days out and
   sends an email. The email contains the deadline and the case title. It does
   **not** contain the denial reason, the treatment, or any clinical detail — a
   reminder lands in an inbox that may be read on a shared screen.

## What goes to Anthropic, and what does not

Document text goes to Anthropic's API for extraction, and argument nodes plus
confirmed facts go for letter prose. There is no way to read a document without
reading it.

What we do about that:

- **No training on user data.** Anthropic's API does not train on API inputs or
  outputs by default. This must be confirmed against the commercial terms in
  force at deploy time and recorded in `docs/DEPLOY.md`.
- **No PHI in LLM call metadata.** The `llm_calls` table stores a **hash** of the
  prompt, never its content. Purpose, model, token counts and latency are
  recorded; the prompt and the completion are not.
- **No case link in LLM call metadata.** `llm_calls` deliberately has no
  `case_id` column. Linking a call to a case is a step towards linking it to a
  diagnosis, and the table's only jobs are enforcing the per-user monthly cap and
  showing what the LLM cost.

## No PHI in logs

- The application logs request method, path, status and duration. It does not log
  request or response bodies.
- No log statement interpolates `extracted_text`, an `ExtractedFact.value`, a
  letter body, a document filename, or a case title.
- Problem responses carry user-facing copy and a machine-readable code. They do
  not echo submitted values back into the log.
- Unhandled exceptions are logged with a traceback and no request body.
- `GET /healthz` reports which services are configured as booleans only — never
  a key, never a URL. Tested in `tests/test_health.py`.
- Verifying this is a phase 7 deliverable with a test behind it, not an assertion.

## Access control

Two independent layers, deliberately:

1. **The API is the enforcement point.** `user_id` comes from the `sub` claim of
   a JWT whose signature, expiry and audience have all been verified. It is never
   read from a path, query or body parameter. Every query scopes by it.
2. **RLS is the backstop.** Row Level Security is enabled on all 14 tables,
   scoped to `auth.uid()` through `cases.user_id`. The backend uses the
   service-role key and therefore bypasses RLS, so layer 1 is what protects
   normal traffic; RLS protects anything that reaches Postgres by another path,
   which is exactly the situation where you want it.

`tests/test_migration_rls.py` applies the real migration to a real Postgres and
asserts that a second user reading the first user's document text gets zero rows,
and that a cross-case write is refused.

## Deletion

`DELETE /me/data` is a hard delete. Rows and storage objects, not a soft flag.

Every table referencing a user or a case does so with `ON DELETE CASCADE`, so
deleting the auth user removes the cases, documents, facts, determinations,
graphs, deadlines, reminders, letters, timeline and LLM call records. A test
asserts nothing is left behind.

**This includes the record the user might later want.** The case timeline is
described in the design brief as "the record the user may need later", and
deletion destroys it along with everything else. That is the correct trade when
someone asks to be forgotten, and the settings screen says so plainly before the
confirmation rather than after.

What deletion does not reach: emails already delivered to the user's inbox, and
anything the user exported and saved themselves.

## What we do not do

- No analytics or advertising trackers on any authenticated screen.
- No third-party scripts in the case workspace.
- No PHI in URLs — no case detail in a query string, where it would reach server
  logs and browser history.
- No sharing, selling or disclosure of user data to third parties. The
  subprocessors are the ones this system needs to work: Supabase (database,
  auth, storage), Anthropic (document reading and prose), the email provider
  (transactional and reminder email), Stripe (payment), and the hosts.
- No account required for the free triage tool.

## What this product is not

A self-help document-preparation and information tool. Not legal advice, not
medical advice, not representation. The user reviews and files everything
themselves. The disclaimer appears in the footer and in every generated letter:

> Appeal Architect prepares documents and explains procedure. It is not legal or
> medical advice, and it does not represent you. You review and file everything
> yourself.

## Status

Phase 1. Implemented: encryption at rest and in transit, RLS on every table with
a test behind it, private buckets, PHI-free `/healthz`, the `llm_calls` schema
with no PHI and no case link.

Not yet implemented, and not claimed: the hard-delete endpoint (phase 7), the
PHI-free-logging verification test (phase 7), the no-training confirmation
against the terms in force (phase 8 deploy checklist). This document will say so
until each one is done.
