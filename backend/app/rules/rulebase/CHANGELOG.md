# Rulebase changelog

Every version records what changed and which sources were consulted. A route
determination stores the version that produced it, so any conclusion can be
reproduced against the exact rules in force when it was computed.

## 1.0.0 — unreleased (phase 1)

Seed tables only; no `.lp` rules yet. The engine arrives in phase 2.

**Every value in `tables/` is `verified=false`.** They are transcribed from the
build spec's seed baseline (§6.2), which itself marks them for verification
against 29 CFR 2560.503-1 and 45 CFR 147.136.

- Federal baseline: internal appeal filing window, insurer response windows
  (pre-service / post-service / urgent), external review request window and
  decision windows, right to free copies of the claim file.
- Inherited from the pre-engine scaffold and transcribed rather than discarded:
  the ERISA self-funded, Medicare Advantage and Medicaid filing windows. All
  three are `active=false` — their plan types are deferred to phase 7.
- `state_ca.csv`, `state_ny.csv`, `state_tx.csv`: created with headers and **zero
  rows**, deliberately. See the comment block in each file.

### Files awaiting a verified source

These are the files to fill in, in priority order:

| File | What is missing |
|---|---|
| `tables/deadlines.csv` | every `verified` flag; the federal baseline needs checking against the two CFR sections |
| `tables/citations.csv` | every `quote` — the operative sentence, transcribed verbatim |
| `tables/required_elements.csv` | every `verified` flag |
| `tables/state_ca.csv` | all rows — CA Health & Safety Code / Insurance Code |
| `tables/state_ny.csv` | all rows — NY Insurance Law §§ 4904–4914 |
| `tables/state_tx.csv` | all rows — TX Insurance Code ch. 4201 |
