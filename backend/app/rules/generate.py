"""CSV → ASP fact generator.

The transcribed legal tables are the authority for every number in the rulebase.
This turns them into `.lp` facts, and **refuses on a malformed row** rather than
emitting something the solver would silently misread. A typo in a day count is a
wrong deadline, so the generator is strict to the point of being annoying.

It also carries the citation and `verified` flag out of the CSV, so the engine
can attach a citation to each conclusion and warn about anything unverified.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from app.domain.route import DayUnit
from app.domain.trace import Citation

RULEBASE_DIR = Path(__file__).resolve().parent / "rulebase"
TABLES_DIR = RULEBASE_DIR / "tables"

VALID_UNITS = {u.value for u in DayUnit}
VALID_TRIGGERS = {
    "denial_date",
    "denial_received_date",
    "final_adverse_date",
    "service_date",
}
VALID_TIMINGS = {"-", "pre", "post", "concurrent", "urgent", "standard"}
VALID_LEVELS = {"internal_1", "internal_2", "external", "expedited_external"}
VALID_APPLIES = {"any", "filer_not_member", "urgent"}
VALID_MANDATORY = {"mandatory", "optional"}

#: Two-letter codes the rulebase has override tables for. `xx` is synthetic.
STATE_TABLES = ("ca", "ny", "tx")
TEST_STATE = "xx"


class RulebaseError(ValueError):
    """A table row the generator will not turn into a fact."""


@dataclass
class DeadlineRow:
    rule_id: str
    item: str
    timing: str
    plan_type: str
    count: int
    unit: str
    trigger: str
    citation: Citation
    verified: bool
    effective_date: str
    active: bool
    note: str


@dataclass
class RequiredRow:
    rule_id: str
    level: str
    key: str
    label: str
    detail: str
    mandatory: str
    applies: str
    citation: Citation
    verified: bool
    active: bool


@dataclass
class StateOverrideRow:
    state: str
    rule_id: str
    item: str
    count: int
    unit: str
    trigger: str
    citation: Citation
    verified: bool
    effective_date: str
    active: bool
    note: str


@dataclass
class Rulebase:
    """Everything read out of `tables/`, ready to be turned into facts."""

    version: str
    deadlines: list[DeadlineRow] = field(default_factory=list)
    required: list[RequiredRow] = field(default_factory=list)
    overrides: list[StateOverrideRow] = field(default_factory=list)
    citations: dict[str, Citation] = field(default_factory=dict)

    def citation_for(self, rule_id: str) -> Citation | None:
        return self.citations.get(rule_id)

    def unverified_rule_ids(self) -> list[str]:
        """Active rules whose value nobody has checked against its source."""
        ids = [r.rule_id for r in self.deadlines if r.active and not r.verified]
        ids += [r.rule_id for r in self.required if r.active and not r.verified]
        ids += [r.rule_id for r in self.overrides if r.active and not r.verified]
        return sorted(set(ids))


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def _rows(path: Path) -> Iterable[dict[str, str]]:
    """CSV rows with `#` comment lines stripped."""
    if not path.is_file():
        raise RulebaseError(f"missing table: {path}")
    text = "".join(
        line
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if not line.lstrip().startswith("#")
    )
    reader = csv.DictReader(text.splitlines())
    for number, row in enumerate(reader, start=2):
        yield {k: (v or "").strip() for k, v in row.items() if k is not None} | {
            "__line__": str(number)
        }


def _require(row: dict[str, str], field_name: str, path: Path) -> str:
    value = row.get(field_name, "")
    if not value:
        raise RulebaseError(
            f"{path.name} line {row['__line__']}: {field_name} is empty, and this "
            "generator will not guess a legal value"
        )
    return value


def _bool(row: dict[str, str], field_name: str, path: Path, *, default: bool) -> bool:
    raw = row.get(field_name, "").lower()
    if raw == "":
        return default
    if raw in {"true", "yes", "1"}:
        return True
    if raw in {"false", "no", "0"}:
        return False
    raise RulebaseError(
        f"{path.name} line {row['__line__']}: {field_name}={raw!r} is not a boolean"
    )


def _int(row: dict[str, str], field_name: str, path: Path) -> int:
    raw = _require(row, field_name, path)
    try:
        value = int(raw)
    except ValueError:
        raise RulebaseError(
            f"{path.name} line {row['__line__']}: {field_name}={raw!r} is not a whole number"
        ) from None
    if value <= 0:
        raise RulebaseError(
            f"{path.name} line {row['__line__']}: {field_name}={value} must be positive -- "
            "a zero or negative window is never what a regulation says"
        )
    return value


def _one_of(row: dict[str, str], field_name: str, allowed: set[str], path: Path) -> str:
    value = _require(row, field_name, path)
    if value not in allowed:
        raise RulebaseError(
            f"{path.name} line {row['__line__']}: {field_name}={value!r} is not one of "
            f"{sorted(allowed)}"
        )
    return value


def _citation(row: dict[str, str], path: Path, verified: bool) -> Citation:
    return Citation(
        source=_require(row, "citation_source", path),
        locator=row.get("citation_locator", ""),
        verified=verified,
    )


def read_citations(path: Path | None = None) -> dict[str, Citation]:
    path = path or TABLES_DIR / "citations.csv"
    out: dict[str, Citation] = {}
    for row in _rows(path):
        rule_id = _require(row, "rule_id", path)
        verified = _bool(row, "verified", path, default=False)
        out[rule_id] = Citation(
            source=_require(row, "source", path),
            locator=row.get("locator", ""),
            title=row.get("title") or None,
            quote=row.get("quote") or None,
            url=row.get("url") or None,
            verified=verified,
        )
    return out


def read_deadlines(path: Path | None = None) -> list[DeadlineRow]:
    path = path or TABLES_DIR / "deadlines.csv"
    out: list[DeadlineRow] = []
    seen: set[str] = set()
    for row in _rows(path):
        rule_id = _require(row, "rule_id", path)
        if rule_id in seen:
            raise RulebaseError(f"{path.name}: duplicate rule_id {rule_id!r}")
        seen.add(rule_id)
        verified = _bool(row, "verified", path, default=False)
        out.append(
            DeadlineRow(
                rule_id=rule_id,
                item=_require(row, "item", path),
                timing=_one_of(row, "timing", VALID_TIMINGS, path),
                plan_type=_require(row, "plan_type", path),
                count=_int(row, "count", path),
                unit=_one_of(row, "unit", VALID_UNITS, path),
                trigger=_one_of(row, "trigger", VALID_TRIGGERS, path),
                citation=_citation(row, path, verified),
                verified=verified,
                effective_date=row.get("effective_date", ""),
                active=_bool(row, "active", path, default=True),
                note=row.get("note", ""),
            )
        )
    if not out:
        raise RulebaseError(f"{path.name} has no rows; the federal baseline cannot be empty")
    return out


def read_required(path: Path | None = None) -> list[RequiredRow]:
    path = path or TABLES_DIR / "required_elements.csv"
    out: list[RequiredRow] = []
    for row in _rows(path):
        verified = _bool(row, "verified", path, default=False)
        out.append(
            RequiredRow(
                rule_id=_require(row, "rule_id", path),
                level=_one_of(row, "level", VALID_LEVELS, path),
                key=_require(row, "key", path),
                label=_require(row, "label", path),
                detail=row.get("detail", ""),
                mandatory=_one_of(row, "mandatory", VALID_MANDATORY, path),
                applies=_one_of(row, "applies", VALID_APPLIES, path),
                citation=_citation(row, path, verified),
                verified=verified,
                active=_bool(row, "active", path, default=True),
            )
        )
    return out


def read_state_overrides(
    *, include_test_state: bool = False, tables_dir: Path | None = None
) -> list[StateOverrideRow]:
    """Override rows for every state table.

    `include_test_state` loads the synthetic `xx` table. Production never does:
    `xx` is not a US state code, so no real user can select it, but keeping it
    out of the default build means a test fixture can never become a live rule.
    """
    tables_dir = tables_dir or TABLES_DIR
    codes = list(STATE_TABLES) + ([TEST_STATE] if include_test_state else [])
    out: list[StateOverrideRow] = []
    for code in codes:
        path = tables_dir / f"state_{code}.csv"
        for row in _rows(path):
            verified = _bool(row, "verified", path, default=False)
            out.append(
                StateOverrideRow(
                    state=code,
                    rule_id=_require(row, "rule_id", path),
                    item=_require(row, "item", path),
                    count=_int(row, "count", path),
                    unit=_one_of(row, "unit", VALID_UNITS, path),
                    trigger=_one_of(row, "trigger", VALID_TRIGGERS, path),
                    citation=_citation(row, path, verified),
                    verified=verified,
                    effective_date=row.get("effective_date", ""),
                    active=_bool(row, "active", path, default=True),
                    note=row.get("note", ""),
                )
            )
    return out


def load_rulebase(*, include_test_state: bool = False) -> Rulebase:
    version = (RULEBASE_DIR / "VERSION").read_text(encoding="utf-8").strip()
    return Rulebase(
        version=version,
        deadlines=read_deadlines(),
        required=read_required(),
        overrides=read_state_overrides(include_test_state=include_test_state),
        citations=read_citations(),
    )


# ---------------------------------------------------------------------------
# Emitting
# ---------------------------------------------------------------------------


def _atom(value: str) -> str:
    """An ASP constant. Lowercased, non-alphanumerics folded to underscore."""
    cleaned = "".join(c if c.isalnum() else "_" for c in value.lower())
    if not cleaned or not cleaned[0].isalpha():
        raise RulebaseError(f"cannot use {value!r} as an ASP constant")
    return cleaned


def _active(flag: bool) -> str:
    return "active" if flag else "inactive"


def to_facts(rulebase: Rulebase) -> str:
    """Render the rulebase as `.lp` facts."""
    lines: list[str] = [
        "%% Generated from rulebase/tables/*.csv by app/rules/generate.py.",
        "%% Do not edit. Change the CSV and regenerate.",
        f"%% rulebase version: {rulebase.version}",
        "",
    ]

    lines.append("%% ---- federal defaults, no timing dependence ----")
    for row in rulebase.deadlines:
        if row.timing != "-":
            continue
        lines.append(
            f"federal_default({_atom(row.item)}, {row.count}, {_atom(row.unit)}, "
            f'{_atom(row.trigger)}, "{row.rule_id}", {_active(row.active)}).'
        )

    lines.append("")
    lines.append("%% ---- federal defaults that depend on timing or urgency ----")
    for row in rulebase.deadlines:
        if row.timing == "-":
            continue
        lines.append(
            f"federal_default_timed({_atom(row.item)}, {_atom(row.timing)}, {row.count}, "
            f'{_atom(row.unit)}, {_atom(row.trigger)}, "{row.rule_id}", '
            f"{_active(row.active)})."
        )

    lines.append("")
    lines.append("%% ---- state overrides ----")
    if not any(r.active for r in rulebase.overrides):
        lines.append("%% (none — the federal baseline governs in every state)")
    for override in rulebase.overrides:
        lines.append(
            f"state_override({_atom(override.state)}, {_atom(override.item)}, "
            f"{override.count}, {_atom(override.unit)}, {_atom(override.trigger)}, "
            f'"{override.rule_id}", {_active(override.active)}).'
        )

    lines.append("")
    lines.append("%% ---- required elements ----")
    for element in rulebase.required:
        lines.append(
            f"required_element({_atom(element.level)}, {_atom(element.key)}, "
            f'"{element.rule_id}", {_atom(element.mandatory)}, '
            f"{_atom(element.applies)}, {_active(element.active)})."
        )

    return "\n".join(lines) + "\n"
