%% semantics.lp — Dung semantics as ASP encodings.
%%
%% An abstract argumentation framework (Dung 1995) is a set of arguments and a
%% binary attack relation. A semantics says which sets of arguments can be held
%% together rationally.
%%
%% Encodings after Egly, Gaggl and Woltran (2010), "Answer-set programming
%% encodings for argumentation frameworks".
%%
%% Input:   arg(A).  attacks(A, B).
%% Output:  in(A).   — the arguments in this extension
%%
%% One file serves all three semantics, selected by an external constant, so the
%% encodings cannot drift apart:
%%     clingo semantics.lp -c semantics=grounded|complete|stable
%%
%% Why these three:
%%   grounded  — unique, sceptical: accept only what you are forced to accept.
%%               This is "Solid ground". It holds whatever the insurer answers.
%%   complete  — enumerated so the solver can take the maximal ones, which are
%%               exactly the preferred extensions. An argument in some preferred
%%               extension but not in grounded is "Worth adding".
%%   stable    — every argument outside the set is attacked by it. Cheap, and
%%               invaluable for testing because the classic hand-worked
%%               frameworks have known stable extensions.

#const semantics = grounded.

#defined arg/1.
#defined attacks/2.

%% ---------------------------------------------------------------------------
%% Shared vocabulary
%% ---------------------------------------------------------------------------

%% How many arguments attack X, and how many of those are defeated.
attacker_total(X, N) :- arg(X), N = #count{ Y : attacks(Y, X) }.
defeated_attackers(X, N) :- arg(X), N = #count{ Y : attacks(Y, X), defeated(Y) }.

%% X is defeated when a member of the set attacks it.
defeated(X) :- in(Y), attacks(Y, X).

%% Every attacker of X is defeated, so the set defends X.
defends(X) :- attacker_total(X, N), defeated_attackers(X, N).

%% ---------------------------------------------------------------------------
%% grounded — the least fixed point, by monotone positive recursion
%% ---------------------------------------------------------------------------
%%
%% There is NO negation in this block, deliberately. The grounded extension is
%% the least fixed point of the characteristic function, and expressing it with
%% negation-as-failure makes the program unstratified: clingo then returns
%% several answer sets where grounded must be unique. Positive recursion
%% (in → defeated → defends → in) is monotone, so the single answer set is the
%% least fixed point, which is exactly the grounded extension.
%%
%% The base case falls out for free: an unattacked argument has
%% attacker_total(X, 0) and defeated_attackers(X, 0), so defends(X) holds
%% immediately.

in(X) :- arg(X), defends(X), semantics = grounded.

%% ---------------------------------------------------------------------------
%% complete — guess a set, then constrain it
%% ---------------------------------------------------------------------------
%%
%% A complete extension is admissible and contains every argument it defends.
%% The preferred extensions are exactly the maximal complete extensions, and
%% solver.py takes the maximal ones — subset-maximality is a property of the
%% whole collection of answer sets, not of any single one, so it belongs there
%% rather than in a constraint here.

{ in(X) } :- arg(X), semantics = complete.

%% Conflict-free.
:- in(X), in(Y), attacks(X, Y), semantics = complete.

%% Admissible: the set defends each of its members.
:- in(X), not defends(X), semantics = complete.

%% Complete: anything the set defends is in it.
:- arg(X), not in(X), defends(X), semantics = complete.

%% ---------------------------------------------------------------------------
%% stable — a conflict-free set that attacks everything outside itself
%% ---------------------------------------------------------------------------

in(X) :- arg(X), not defeated(X), semantics = stable.

#show in/1.
