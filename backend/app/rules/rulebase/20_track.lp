%% 20_track.lp — review levels, in order.
%%
%% The track is standard or expedited, and exactly one holds. "Expedited" does
%% NOT shorten the window the member has to file: under 45 CFR 147.136 the
%% filing window is the same, and what changes is how fast the insurer must
%% answer. Modelling it the other way round would shorten a real deadline on the
%% strength of a self-declaration, which is the opposite of conservative.

track(expedited) :- urgent, supported.
track(standard)  :- not urgent, supported.

because(track(expedited), "fed.track.expedited", (urgent,)) :- track(expedited).
because(track(standard), "fed.track.standard", (not_urgent,)) :- track(standard).

%% ---- levels ---------------------------------------------------------------
level(internal_1) :- supported.
level(external)   :- supported.

because(level(internal_1), "fed.level.internal_1", (supported,)) :- level(internal_1).
because(level(external), "fed.level.external", (supported,)) :- level(external).

step(1, internal_1) :- level(internal_1).
step(2, external)   :- level(external).

because(step(1, internal_1), "fed.step.internal_first",
        (level(internal_1),)) :- step(1, internal_1).
because(step(2, external), "fed.step.external_after_internal",
        (level(external), level(internal_1))) :- step(2, external).

%% ---- who acts at each level ----------------------------------------------
who_files(internal_1, member_files)        :- level(internal_1), filer(member).
who_files(internal_1, representative_files) :- level(internal_1), filer(authorized_rep).
who_files(internal_1, provider_files)      :- level(internal_1), filer(provider).
who_files(external, member_requests)       :- level(external).

because(who_files(internal_1, W), "fed.who_files.internal", (filer_stated,)) :-
    who_files(internal_1, W).
because(who_files(external, member_requests), "fed.who_files.external",
        (level(external),)) :- who_files(external, member_requests).

%% ---- who decides ----------------------------------------------------------
review_body(internal_1, insurer_internal_reviewer) :- level(internal_1).
review_body(external, independent_review_organisation) :- level(external).

because(review_body(internal_1, insurer_internal_reviewer),
        "fed.review_body.internal", (level(internal_1),)) :- level(internal_1).
because(review_body(external, independent_review_organisation),
        "fed.review_body.external", (level(external),)) :- level(external).
