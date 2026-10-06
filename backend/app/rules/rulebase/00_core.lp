%% 00_core.lp — vocabulary and the justification constraint.
%%
%% Every derived atom must carry because(Conclusion, RuleId, Premises). The
%% integrity constraints at the bottom of this file make a model without full
%% justification UNSATISFIABLE, so a conclusion the rulebase cannot justify is
%% not a conclusion it can reach.
%%
%% Rule id namespaces: fed.* aca.* erisa.* ca.* ny.* tx.* xx.* (xx = test state)

#const unsupported_plan_warning = "plan_type_unsupported".

%% ---- input predicates, supplied by app/rules/facts.py ----------------------
%%   plan_type/1          aca_marketplace | employer_fully_insured | ...
%%   state/1              two-letter code, lowercase atom
%%   service_timing/1     pre | post | concurrent
%%   denial_reason/1      one per stated reason
%%   urgent/0             present only when the member declared medical urgency
%%   filer/1              member | authorized_rep | provider
%%   has_received_date/0  present when the member told us when the letter arrived

#defined plan_type/1.
#defined state/1.
#defined service_timing/1.
#defined denial_reason/1.
#defined urgent/0.
#defined filer/1.
#defined has_received_date/0.

%% ---- generated from rulebase/tables/*.csv ---------------------------------
#defined federal_default/6.
#defined federal_default_timed/7.
#defined state_override/7.
#defined required_element/6.
#defined response_window/4.

%% ---- derived --------------------------------------------------------------
#defined track/1.
#defined level/1.
#defined step/2.
#defined deadline_spec/6.
#defined requires/3.
#defined review_body/2.
#defined who_files/2.
#defined warning/1.
#defined because/3.
#defined supported/0.

%% Anything with a because/3 is justified.
justified(X) :- because(X, _, _).

%% ---- the justification constraints ----------------------------------------
%% A derived atom with no justification makes the program unsatisfiable. This is
%% what turns "every conclusion carries a trace" from a convention into a
%% property of the rulebase.
:- track(T),               not justified(track(T)).
:- level(L),               not justified(level(L)).
:- step(O, L),             not justified(step(O, L)).
:- deadline_spec(I,C,U,T,S,R), not justified(deadline_spec(I,C,U,T,S,R)).
:- requires(L, K, R),      not justified(requires(L, K, R)).
:- review_body(L, B),      not justified(review_body(L, B)).
:- who_files(L, W),        not justified(who_files(L, W)).

#show track/1.
#show level/1.
#show step/2.
#show deadline_spec/6.
#show requires/3.
#show review_body/2.
#show who_files/2.
#show warning/1.
#show because/3.
#show supported/0.
