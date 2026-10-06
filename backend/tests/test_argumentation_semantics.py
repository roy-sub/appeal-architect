"""The semantics encodings, against hand-worked frameworks.

A semantics encoding that quietly drifts would relabel a user's argument from
"Solid ground" to "Worth adding" with no visible symptom. So the fixtures in
tests/af/frameworks.json are compared as sets, exactly, on all three semantics,
and each one carries the reasoning that produced it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.argumentation.solver import (
    Framework,
    grounded_extension,
    preferred_extensions,
    solve_framework,
    stable_extensions,
)

FIXTURES = json.loads(
    (Path(__file__).resolve().parent / "af" / "frameworks.json").read_text(encoding="utf-8")
)


def _framework(case: dict) -> Framework:
    return Framework.of(case["arguments"], [tuple(a) for a in case["attacks"]])


def _sets(raw: list[list[str]]) -> set[frozenset[str]]:
    return {frozenset(s) for s in raw}


def test_fixtures_are_present() -> None:
    assert len(FIXTURES) >= 12, "the classic cases should all be covered"
    names = {case["name"] for case in FIXTURES}
    for essential in (
        "even_cycle_two",
        "odd_cycle_three",
        "self_attack",
        "reinstatement",
        "floating_defeat",
    ):
        assert essential in names, f"missing the classic {essential} case"
    for case in FIXTURES:
        assert case.get("why"), f"{case['name']} has no stated reasoning"


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_grounded_matches_exactly(case: dict) -> None:
    assert grounded_extension(_framework(case)) == frozenset(case["grounded"]), case["why"]


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_preferred_matches_exactly(case: dict) -> None:
    got = set(preferred_extensions(_framework(case)))
    assert got == _sets(case["preferred"]), case["why"]


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_stable_matches_exactly(case: dict) -> None:
    got = set(stable_extensions(_framework(case)))
    assert got == _sets(case["stable"]), case["why"]


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_grounded_is_contained_in_every_preferred_extension(case: dict) -> None:
    """A theorem of Dung 1995, so a useful independent check on the encodings."""
    framework = _framework(case)
    grounded = grounded_extension(framework)
    for extension in preferred_extensions(framework):
        assert grounded <= extension, (
            f"{case['name']}: grounded {sorted(grounded)} is not contained in "
            f"preferred {sorted(extension)}"
        )


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_every_stable_extension_is_preferred(case: dict) -> None:
    """Also a theorem: stable extensions are preferred extensions."""
    framework = _framework(case)
    preferred = set(preferred_extensions(framework))
    for extension in stable_extensions(framework):
        assert extension in preferred, (
            f"{case['name']}: stable {sorted(extension)} is not among the preferred"
        )


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_every_extension_is_conflict_free(case: dict) -> None:
    """The most basic property. If this ever fails, nothing else means anything."""
    framework = _framework(case)
    extensions = solve_framework(framework)
    candidates = [extensions.grounded, *extensions.preferred, *extensions.stable]
    for extension in candidates:
        for source, target in framework.attacks:
            assert not (source in extension and target in extension), (
                f"{case['name']}: {sorted(extension)} contains the attack {source} -> {target}"
            )


def test_an_odd_cycle_has_no_stable_extension() -> None:
    """Pinned on its own, because it is the reason three semantics are needed.

    A product that computed only stable extensions would tell the user there is
    no defensible position at all in this shape.
    """
    framework = Framework.of(["a", "b", "c"], [("a", "b"), ("b", "c"), ("c", "a")])
    assert stable_extensions(framework) == ()
    assert preferred_extensions(framework) == (frozenset(),)


def test_grounded_is_unique_and_the_runner_asserts_it() -> None:
    """Grounded is unique by definition, so the solver asks for two and checks."""
    for case in FIXTURES:
        framework = _framework(case)
        assert isinstance(grounded_extension(framework), frozenset)


def test_a_dangling_attack_is_refused() -> None:
    """An attack naming an argument not in the framework is a builder bug.

    Silently ignoring it would make the solver compute over a framework that
    differs from the one the user is shown.
    """
    with pytest.raises(ValueError, match="not in the framework"):
        Framework.of(["a"], [("a", "ghost")])


def test_worth_adding_is_credulous_minus_sceptical() -> None:
    """The definition the product's second tier rests on."""
    framework = Framework.of(["a", "b"], [("a", "b"), ("b", "a")])
    extensions = solve_framework(framework)
    assert extensions.grounded == frozenset()
    assert extensions.worth_adding == frozenset({"a", "b"})


def test_defeated_is_in_no_preferred_extension() -> None:
    """Floating defeat: c loses whichever of a or b survives."""
    framework = Framework.of(["a", "b", "c"], [("a", "b"), ("b", "a"), ("a", "c"), ("b", "c")])
    extensions = solve_framework(framework)
    assert extensions.defeated(framework.arguments) == frozenset({"c"})
