# Rulebase

The engine is built. `app/rules/rulebase/*.lp` holds the rules, `runner.py`
solves them with clingo and refuses a non-unique or unjustified answer set, and
`deadlines.py` does the date arithmetic against a holiday calendar tested on
5 U.S.C. § 6103. What follows is what the rules are allowed to say, and what is
still missing from them.

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

## Four of the six plan types have no route

`10_plan_type.lp` admits `aca_marketplace` and `employer_fully_insured`. The
other four produce no track, no steps and no deadlines, and a warning saying so.

`employer_self_funded`, `medicare_advantage` and `medicaid` each have their
filing window transcribed in `tables/deadlines.csv` with `active=false`. Flipping
that flag is **not** enough to turn them on, and the flag is not the hard part:

- A self-funded ERISA plan appeals under 29 CFR 2560.503-1 rather than 45 CFR
  147.136, so the citations on every step change even where the counts do not.
- Medicare Advantage runs reconsideration → independent review entity → ALJ →
  Council → judicial review. Medicaid managed care runs plan appeal → state fair
  hearing. **Neither ends in ACA external review.** Routing them through
  `20_track.lp` as it stands would produce a confidently wrong track, which is
  the one failure this rulebase exists to prevent.

So each needs its own route shape read out of its own regulation, not a flag.
Until then the product says it cannot work the route out, and the rest of the
case — arguments, evidence, letter — still runs, because none of it depends on
the plan type.

`unknown` is separate: it is a question the user has not answered yet, not a gap
in the rulebase.
