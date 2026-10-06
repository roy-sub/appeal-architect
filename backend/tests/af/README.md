# Argumentation framework fixtures

Hand-built frameworks with extensions worked out on paper, including the classic
non-trivial cases: even and odd attack cycles, self-attacking arguments,
reinstatement, and floating defeat.

The solver's output must match these **exactly**, on all three semantics. A
semantics encoding that quietly drifts is the kind of bug that would relabel a
user's argument from "Solid ground" to "Worth adding" with no visible symptom,
so these are compared as sets, not spot-checked.

Each fixture carries `why`, explaining the reasoning, so a future reader can
check the expectation against Dung 1995 rather than trusting it.
