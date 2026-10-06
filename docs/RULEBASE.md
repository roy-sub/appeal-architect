# Rulebase

> **Phase 2 deliverable.** This file is a stub. The rules engine does not exist
> yet; there are no `.lp` files. What does exist is the seed tables and the
> promise below.

## The absolute rule

Every deadline, response window and required element comes from a transcribed
source with a citation. No value is improvised, ever.

Tables live in `backend/app/rules/rulebase/tables/*.csv`. Each carries a header
naming its source, a `verified` flag, and an `effective_date`. A generator turns
the CSVs into `.lp` facts and refuses on a malformed row.

## Every value currently in the rulebase is UNVERIFIED

`verified=false` means nobody has read that value in the source it cites.

Unverified values are **not** hidden and **not** treated as correct. They appear
as an `UNVERIFIED` warning on the route determination and as a banner in the UI.

`backend/app/rules/rulebase/CHANGELOG.md` lists the files awaiting a source. In
priority order:

| File | What is missing |
|---|---|
| `tables/deadlines.csv` | every `verified` flag — the federal baseline needs checking against 45 CFR 147.136 and 29 CFR 2560.503-1 |
| `tables/citations.csv` | every `quote` — the operative sentence, transcribed verbatim |
| `tables/required_elements.csv` | every `verified` flag |
| `tables/state_ca.csv` | all rows — CA Health & Safety Code / Insurance Code |
| `tables/state_ny.csv` | all rows — NY Insurance Law §§ 4904–4914 |
| `tables/state_tx.csv` | all rows — TX Insurance Code ch. 4201 |

## The state tables are empty on purpose

`state_ca.csv`, `state_ny.csv` and `state_tx.csv` have headers and zero rows.

With no override row, the defeasible federal-default pattern falls through to the
federal baseline. That is correct and honest.

They are empty because we have no state statute source. A plausible-looking
invented state deadline, displayed to a user with a citation beside it as the
date their rights expire, is the most harmful artefact this codebase could
contain. So the files are wired and empty rather than filled and wrong.

The override *mechanism* is proven by a synthetic state `XX` in the golden tests,
which exercises the full federal-default-versus-state-override path without any
real value being invented.

## To be written in phase 2

- `00_core.lp`, `10_plan_type.lp`, `20_track.lp`, `30_deadlines.lp`,
  `40_required.lp`, `50_expedited.lp`
- `90_state_ca.lp`, `90_state_ny.lp`, `90_state_tx.lp`
- The CSV→LP generator and its malformed-row refusal
- `deadlines.py` — pure date arithmetic, and `calendar.py` — the holiday adapter
- `tests/golden/` worked examples, and `tests/test_deadlines.py`
