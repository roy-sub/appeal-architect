"""The argumentation solver. PURE: no network, no LLM, no database.

Computes grounded, preferred and stable extensions of an abstract argumentation
framework via the ASP encodings in ``semantics.lp``.

The application never asserts that an argument is defeated. The solver computes
it. That is what makes "Solid ground" a claim the product can stand behind
rather than a label it hands out.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import clingo

SEMANTICS_PATH = Path(__file__).resolve().parent / "semantics.lp"


@dataclass(frozen=True)
class Framework:
    """A Dung abstract argumentation framework."""

    arguments: frozenset[str]
    attacks: frozenset[tuple[str, str]]

    def __post_init__(self) -> None:
        unknown = {name for attack in self.attacks for name in attack if name not in self.arguments}
        if unknown:
            raise ValueError(f"attacks reference arguments not in the framework: {sorted(unknown)}")

    @classmethod
    def of(cls, arguments: list[str] | set[str], attacks: list[tuple[str, str]]) -> Framework:
        return cls(frozenset(arguments), frozenset(attacks))

    def to_facts(self) -> str:
        """Render as ASP facts. Ids are quoted, so any string is a valid id."""
        lines = [f'arg("{a}").' for a in sorted(self.arguments)]
        lines += [f'attacks("{a}","{b}").' for a, b in sorted(self.attacks)]
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Extensions:
    """What the solver computed, for one framework."""

    grounded: frozenset[str]
    preferred: tuple[frozenset[str], ...]
    stable: tuple[frozenset[str], ...]

    @property
    def worth_adding(self) -> frozenset[str]:
        """In some preferred extension but not in grounded.

        Holds under some readings but not all, which is exactly what the design
        calls "Worth adding": useful extra weight, not the main point.
        """
        credulous: set[str] = set()
        for extension in self.preferred:
            credulous |= extension
        return frozenset(credulous - self.grounded)

    def defeated(self, all_arguments: frozenset[str]) -> frozenset[str]:
        """In no preferred extension: there is no reading on which it holds.

        Kept visible to the user as "Left out", so they can see it was
        considered rather than wondering whether we missed it.
        """
        credulous: set[str] = set()
        for extension in self.preferred:
            credulous |= extension
        return frozenset(all_arguments - credulous)


@lru_cache(maxsize=1)
def _encoding() -> str:
    return SEMANTICS_PATH.read_text(encoding="utf-8")


def _solve(framework: Framework, semantics: str, *, limit: int = 0) -> list[frozenset[str]]:
    control = clingo.Control([f"--models={limit}", "-c", f"semantics={semantics}", "--warn=none"])
    control.add("base", [], _encoding() + "\n" + framework.to_facts())
    control.ground([("base", [])])

    found: list[frozenset[str]] = []
    with control.solve(yield_=True) as handle:
        for model in handle:
            found.append(
                frozenset(symbol.arguments[0].string for symbol in model.symbols(shown=True))
            )
    return found


def grounded_extension(framework: Framework) -> frozenset[str]:
    """The unique grounded extension.

    Asked for two models and asserts one, because grounded is unique by
    definition: a second answer set would mean the encoding has gone wrong.
    """
    models = _solve(framework, "grounded", limit=2)
    if len(models) != 1:
        raise RuntimeError(
            f"grounded is unique by definition but the encoding returned "
            f"{len(models)} answer sets — see semantics.lp"
        )
    return models[0]


def preferred_extensions(framework: Framework) -> tuple[frozenset[str], ...]:
    """The preferred extensions: the maximal complete extensions.

    Subset-maximality is a property of the whole collection of answer sets
    rather than of any one of them, so the encoding enumerates complete
    extensions and the maximal ones are selected here.
    """
    complete = _solve(framework, "complete", limit=0)
    maximal = [
        extension for extension in complete if not any(extension < other for other in complete)
    ]
    return tuple(sorted(maximal, key=lambda s: (-len(s), sorted(s))))


def stable_extensions(framework: Framework) -> tuple[frozenset[str], ...]:
    """The stable extensions. There may be none — an odd attack cycle has none."""
    models = _solve(framework, "stable", limit=0)
    return tuple(sorted(models, key=lambda s: (-len(s), sorted(s))))


def solve_framework(framework: Framework) -> Extensions:
    """All three semantics for one framework."""
    return Extensions(
        grounded=grounded_extension(framework),
        preferred=preferred_extensions(framework),
        stable=stable_extensions(framework),
    )
