"""The CSV→LP generator refuses malformed rows.

A typo in a day count is a wrong deadline, so the generator is strict to the
point of being annoying. These tests are the record of what it refuses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.rules import generate
from app.rules.generate import RulebaseError

HEADER = (
    "rule_id,item,timing,plan_type,count,unit,trigger,citation_source,"
    "citation_locator,verified,effective_date,active,note\n"
)
GOOD = "fed.x,internal_appeal,-,*,180,calendar,denial_date,45 CFR 147.136,(b)(2),false,,true,\n"


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "deadlines.csv"
    path.write_text("# a comment line, skipped\n" + HEADER + body, encoding="utf-8")
    return path


def test_a_good_row_reads(tmp_path: Path) -> None:
    rows = generate.read_deadlines(_write(tmp_path, GOOD))
    assert len(rows) == 1
    assert rows[0].count == 180 and rows[0].unit == "calendar"
    assert rows[0].verified is False


def test_comment_lines_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "deadlines.csv"
    path.write_text(f"# one\n# two\n{HEADER}{GOOD}# three\n", encoding="utf-8")
    assert len(generate.read_deadlines(path)) == 1


@pytest.mark.parametrize(
    ("bad", "expected"),
    [
        (GOOD.replace(",180,", ",0,"), "must be positive"),
        (GOOD.replace(",180,", ",-5,"), "must be positive"),
        (GOOD.replace(",180,", ",lots,"), "not a whole number"),
        (GOOD.replace(",180,", ",,"), "is empty"),
        (GOOD.replace("calendar", "fortnights"), "not one of"),
        (GOOD.replace("denial_date", "whenever"), "not one of"),
        (GOOD.replace(",-,*,", ",sometimes,*,"), "not one of"),
        (GOOD.replace("45 CFR 147.136", ""), "is empty"),
        (GOOD.replace(",false,,true,", ",maybe,,true,"), "not a boolean"),
        (GOOD.replace("fed.x,", ","), "is empty"),
    ],
    ids=[
        "zero count",
        "negative count",
        "non-numeric count",
        "empty count",
        "unknown unit",
        "unknown trigger",
        "unknown timing",
        "missing citation",
        "non-boolean verified",
        "missing rule id",
    ],
)
def test_malformed_rows_are_refused(tmp_path: Path, bad: str, expected: str) -> None:
    """Each of these would otherwise become a silently wrong legal value."""
    with pytest.raises(RulebaseError, match=expected):
        generate.read_deadlines(_write(tmp_path, bad))


def test_a_duplicate_rule_id_is_refused(tmp_path: Path) -> None:
    """Two rows with one id means the solver sees two conflicting windows."""
    with pytest.raises(RulebaseError, match="duplicate rule_id"):
        generate.read_deadlines(_write(tmp_path, GOOD + GOOD))


def test_an_empty_federal_table_is_refused(tmp_path: Path) -> None:
    """Empty state tables are correct; an empty federal baseline is a broken build."""
    with pytest.raises(RulebaseError, match="cannot be empty"):
        generate.read_deadlines(_write(tmp_path, ""))


def test_a_missing_table_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RulebaseError, match="missing table"):
        generate.read_deadlines(tmp_path / "nope.csv")


def test_the_real_tables_all_read() -> None:
    rulebase = generate.load_rulebase(include_test_state=True)
    assert rulebase.version
    assert rulebase.deadlines and rulebase.required
    assert rulebase.citations


def test_every_active_rule_has_a_citation_row() -> None:
    """A rule the engine can use but citations.csv does not list would render a
    conclusion with no source. Caught here rather than in the UI."""
    rulebase = generate.load_rulebase(include_test_state=True)
    active = {r.rule_id for r in rulebase.deadlines if r.active}
    active |= {r.rule_id for r in rulebase.required if r.active}
    active |= {r.rule_id for r in rulebase.overrides if r.active}
    missing = sorted(active - set(rulebase.citations))
    assert not missing, f"active rules absent from citations.csv: {missing}"


def test_generated_facts_are_valid_asp() -> None:
    """The generator's output has to ground, or the rulebase will not load."""
    import clingo

    rulebase = generate.load_rulebase(include_test_state=True)
    control = clingo.Control(["--models=1"])
    control.add("base", [], generate.to_facts(rulebase))
    control.ground([("base", [])])  # raises on a syntax error
    with control.solve(yield_=True) as handle:
        assert next(iter(handle), None) is not None


def test_inactive_rows_are_marked_inactive_in_the_facts() -> None:
    """Deferred plan types are transcribed but must not fire."""
    rulebase = generate.load_rulebase()
    facts = generate.to_facts(rulebase)
    assert '"ma.redetermination.window", inactive' in facts
    assert '"medicaid.plan_appeal.window", inactive' in facts
    assert '"erisa.internal_appeal.window", inactive' in facts
    assert '"fed.internal_appeal.window", active' in facts


def test_an_unusable_constant_is_refused() -> None:
    with pytest.raises(RulebaseError, match="as an ASP constant"):
        generate._atom("123")
