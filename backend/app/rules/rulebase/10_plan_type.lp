%% 10_plan_type.lp — which plans the rulebase can route.
%%
%% An unsupported plan type does not produce a guessed route. It produces no
%% route and a warning, because a confident wrong track is worse than an honest
%% "we cannot work this out yet".

%% Phase 2 scope: the ACA individual market and fully-insured employer plans.
%% Self-funded ERISA, Medicare Advantage and Medicaid are deferred (spec 5).
in_scope(aca_marketplace).
in_scope(employer_fully_insured).

supported :- plan_type(P), in_scope(P).

warning(unsupported_plan_warning) :- plan_type(P), not in_scope(P).
warning("plan_type_unknown") :- plan_type(unknown).

%% A fully-insured employer plan is a group health plan, and a group plan may
%% operate TWO levels of internal appeal where the individual market has one.
%% We model one level and say so: filing the first level on time is correct
%% either way, so the conservative route is also the safe one.
warning("employer_plan_may_have_second_internal_level") :-
    plan_type(employer_fully_insured).
