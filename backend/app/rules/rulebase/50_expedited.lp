%% 50_expedited.lp — the expedited path.
%%
%% Expedited review is available when delay would seriously jeopardise the
%% member's health. That is the member's own declaration, so a route that relies
%% on it says so in a warning: the product never quietly changes a legal
%% conclusion on the strength of a checkbox.

level(expedited_external) :- track(expedited).
because(level(expedited_external), "fed.level.expedited_external",
        (track(expedited),)) :- level(expedited_external).

step(3, expedited_external) :- level(expedited_external).
because(step(3, expedited_external), "fed.step.expedited_external_available",
        (level(expedited_external), track(expedited))) :- step(3, expedited_external).

who_files(expedited_external, member_requests) :- level(expedited_external).
because(who_files(expedited_external, member_requests),
        "fed.who_files.expedited_external", (level(expedited_external),)) :-
    who_files(expedited_external, member_requests).

review_body(expedited_external, independent_review_organisation) :-
    level(expedited_external).
because(review_body(expedited_external, independent_review_organisation),
        "fed.review_body.expedited_external", (level(expedited_external),)) :-
    level(expedited_external).

%% Expedited internal and external review may run at the same time rather than
%% in sequence, which is a real advantage and easy to miss.
warning("expedited_internal_and_external_may_run_together") :- track(expedited).

%% The track rests on the member's declaration, not on anything we verified.
warning("expedited_track_from_your_own_urgency_statement") :- track(expedited).
