%% 40_required.lp — what each filing must contain.

requires(Level, Key, RuleId) :-
    required_element(Level, Key, RuleId, Mandatory, Applies, active),
    applies(Applies),
    level(Level),
    Mandatory = mandatory.

requires(Level, Key, RuleId) :-
    required_element(Level, Key, RuleId, optional, Applies, active),
    applies(Applies),
    level(Level).

because(requires(Level, Key, RuleId), RuleId, (level(Level),)) :-
    requires(Level, Key, RuleId).

%% `applies` gates an element on the case. `any` is unconditional; the others
%% name the condition the element depends on.
applies(any).
applies(filer_not_member) :- filer(authorized_rep).
applies(filer_not_member) :- filer(provider).
applies(urgent) :- urgent.
