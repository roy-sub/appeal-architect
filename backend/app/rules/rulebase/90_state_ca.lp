%% 90_state_ca.lp — California overrides.
%%
%% The override RULES live here; the override VALUES live in
%% tables/state_ca.csv, which is intentionally empty. With no row, nothing in
%% this file fires and the federal baseline governs — which is the correct and
%% honest outcome, not a gap.
%%
%% The generic federal-default / state-override pattern in 30_deadlines.lp
%% already consumes state_override/7 for every state, so a CA-specific rule is
%% needed only for something California does that no other state does. Nothing
%% here yet. Do not add a value to the CSV you have not read in the statute.

state_layer(ca).
