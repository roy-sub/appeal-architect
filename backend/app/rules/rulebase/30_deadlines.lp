%% 30_deadlines.lp — the federal default, and how a state overrides it.
%%
%% The pattern, written defeasibly so a state table can displace a federal row
%% without either file knowing about the other:
%%
%%     federal applies unless a state override for the same item exists
%%
%% With no override row present — which is the case for every state today — the
%% federal baseline governs. That is why the empty state tables are correct and
%% not merely unfinished.
%%
%% deadline_spec(Item, Count, Unit, Trigger, Source, RuleId)
%%   Source is `federal` or the two-letter state atom, so the UI can say which
%%   layer produced the number.

%% ---- items that do not depend on timing or urgency ------------------------
deadline_spec(Item, Count, Unit, Trigger, federal, RuleId) :-
    federal_default(Item, Count, Unit, Trigger, RuleId, active),
    supported,
    not has_state_override(Item).

because(deadline_spec(Item, Count, Unit, Trigger, federal, RuleId),
        RuleId, (federal_default(Item, Count),)) :-
    deadline_spec(Item, Count, Unit, Trigger, federal, RuleId).

%% ---- a state override displaces the federal row --------------------------
has_state_override(Item) :- state_override(S, Item, _, _, _, _, active), state(S).

deadline_spec(Item, Count, Unit, Trigger, S, RuleId) :-
    state_override(S, Item, Count, Unit, Trigger, RuleId, active),
    state(S),
    supported.

because(deadline_spec(Item, Count, Unit, Trigger, S, RuleId),
        RuleId, (state_override(S, Item, Count),)) :-
    deadline_spec(Item, Count, Unit, Trigger, S, RuleId),
    S != federal.

%% ---- the insurer's response window depends on service timing -------------
%% Pre-service and post-service claims get different windows, and an expedited
%% request gets a much shorter one. The timing is a confirmed fact, never
%% inferred from the dates.
deadline_spec(insurer_response, Count, Unit, Trigger, federal, RuleId) :-
    federal_default_timed(insurer_response, Timing, Count, Unit, Trigger, RuleId, active),
    service_timing(Timing),
    track(standard),
    supported.

deadline_spec(insurer_response, Count, Unit, Trigger, federal, RuleId) :-
    federal_default_timed(insurer_response, urgent, Count, Unit, Trigger, RuleId, active),
    track(expedited),
    supported.

because(deadline_spec(insurer_response, Count, Unit, Trigger, federal, RuleId),
        RuleId, (service_timing_confirmed, track_determined)) :-
    deadline_spec(insurer_response, Count, Unit, Trigger, federal, RuleId).

%% ---- the external review decision window ---------------------------------
deadline_spec(external_review_decision, Count, Unit, Trigger, federal, RuleId) :-
    federal_default_timed(external_review_decision, standard, Count, Unit, Trigger,
                          RuleId, active),
    track(standard),
    supported.

deadline_spec(external_review_decision, Count, Unit, Trigger, federal, RuleId) :-
    federal_default_timed(external_review_decision, urgent, Count, Unit, Trigger,
                          RuleId, active),
    track(expedited),
    supported.

%% ---- disclosure when the receipt date is unknown -------------------------
%% The federal filing window counts from receipt of the notice. When we do not
%% know that date the engine counts from the letter's own date, which is earlier
%% and therefore safer, and this warning makes the UI say so.
warning("filing_window_counted_from_letter_date") :-
    deadline_spec(internal_appeal, _, _, denial_received_date, _, _),
    not has_received_date.
