"""The neurosymbolic boundary, enforced.

The product's defining claim is that the LLM never computes a route, a deadline,
or whether an argument holds. This test is what makes that claim checkable:

1. ``app/rules/**`` and ``app/argumentation/**`` may import only the standard
   library, an allow-list of pure third-party packages, and ``app.domain``.
   Nothing that can reach a model, a network or a database.
2. The restriction is applied to the **transitive** closure, not just direct
   imports. A direct-import check leaks: ``app.domain`` is permitted, so anything
   ``app.domain`` imports would reach the engine unchecked.
3. ``app/services/llm.py`` -- the only module allowed to import ``anthropic`` --
   must not import either engine runner, and must not write to the tables that
   store conclusions.

If this test goes red, the architecture has been violated. Do not skip it, do not
mark it xfail, and do not add to the allow-list without reading docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = BACKEND_ROOT / "app"

#: The packages the pure engine is allowed to reach.
#:
#: Widening this list is an architectural decision, not a convenience. Each entry
#: has to be a pure computation or data-parsing library: no network client, no
#: database driver, no model SDK, and nothing that could acquire one as a
#: dependency. Record the reason when adding one.
#:
#:   clingo, clorm        the ASP solver and its ORM (spec 4.1)
#:   pydantic             the domain models (spec 4.1)
#:   dateutil             month arithmetic (spec 4.1)
#:   holidays             US federal holidays, in place of `workalendar`, which
#:                        cannot be installed here (PLAN.md Q1)
#:   yaml                 the scheme library is YAML files on disk (spec 7.2).
#:                        Parsing only; the builder uses safe_load, so no
#:                        arbitrary object construction.
#:   typing_extensions    typing backports
ALLOWED_THIRD_PARTY = frozenset(
    {
        "clingo",
        "clorm",
        "pydantic",
        "dateutil",
        "holidays",
        "yaml",
        "typing_extensions",
    }
)

#: Modules that must never appear anywhere in the engine's import closure.
FORBIDDEN = frozenset(
    {
        "anthropic",
        "httpx",
        "requests",
        "urllib3",
        "aiohttp",
        "supabase",
        "openai",
        "app.services.llm",
        "app.db",
    }
)

#: The two packages that must stay pure.
PURE_PACKAGES = ("app.rules", "app.argumentation")

#: Tables that hold engine conclusions. The LLM module may not write to them.
CONCLUSION_TABLES = ("route_determinations", "argument_graphs")


def _stdlib_names() -> frozenset[str]:
    import sys

    return frozenset(sys.stdlib_module_names)


STDLIB = _stdlib_names()


def _module_name(path: Path) -> str:
    rel = path.relative_to(BACKEND_ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports_of(path: Path) -> set[str]:
    """Every module name imported by this file, with relative imports resolved."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    here = _module_name(path)
    package = here if path.name == "__init__.py" else here.rsplit(".", 1)[0]

    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # Resolve `from . import x` / `from ..y import z` against this file.
                base = package.split(".")
                base = base[: len(base) - (node.level - 1)] if node.level > 1 else base
                prefix = ".".join(base)
                target = f"{prefix}.{node.module}" if node.module else prefix
            else:
                target = node.module or ""
            if target:
                found.add(target)
                for alias in node.names:
                    # `from app.db import client` -- the imported name may itself
                    # be a submodule, so record both.
                    found.add(f"{target}.{alias.name}")
    return found


def _top(module: str) -> str:
    return module.split(".", 1)[0]


def _is_internal(module: str) -> bool:
    return module == "app" or module.startswith("app.")


def _path_for(module: str) -> Path | None:
    """Resolve an internal module name to a file on disk, if it is one."""
    rel = Path(*module.split("."))
    for candidate in (BACKEND_ROOT / rel.with_suffix(".py"), BACKEND_ROOT / rel / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _engine_files() -> list[Path]:
    files: list[Path] = []
    for package in PURE_PACKAGES:
        root = BACKEND_ROOT / Path(*package.split("."))
        files.extend(sorted(root.rglob("*.py")))
    return files


def _violations(start_files: list[Path]) -> list[str]:
    """Walk the transitive import closure and report every rule break."""
    problems: list[str] = []
    seen: set[Path] = set()
    queue = list(start_files)

    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        origin = _module_name(path)

        for imported in sorted(_imports_of(path)):
            for bad in FORBIDDEN:
                if imported == bad or imported.startswith(f"{bad}."):
                    problems.append(f"{origin} imports forbidden module {imported!r}")

            if _is_internal(imported):
                # Internal imports are followed, so a violation two hops away is
                # still caught.
                nxt = _path_for(imported)
                if nxt is not None and nxt not in seen:
                    queue.append(nxt)
                continue

            top = _top(imported)
            if top in STDLIB or top in ALLOWED_THIRD_PARTY:
                continue
            problems.append(
                f"{origin} imports {imported!r}, which is neither stdlib nor on the "
                f"engine's allow-list ({', '.join(sorted(ALLOWED_THIRD_PARTY))})"
            )

    return problems


def test_engine_packages_exist() -> None:
    """Guard against the whole test vacuously passing on an empty tree."""
    files = _engine_files()
    assert files, "no files found under app/rules or app/argumentation"
    for package in PURE_PACKAGES:
        root = BACKEND_ROOT / Path(*package.split("."))
        assert (root / "__init__.py").is_file(), f"{package} is not a package"


def test_rules_and_argumentation_are_pure() -> None:
    """The invariant: no path from the engine to a model, a network or a database."""
    problems = _violations(_engine_files())
    assert not problems, "neurosymbolic boundary violated:\n  " + "\n  ".join(problems)


def test_domain_is_pure() -> None:
    """``app.domain`` is importable by the engine, so it must be pure too.

    Without this, the allow-list on ``app.domain`` would be a hole straight
    through the boundary.
    """
    files = sorted((APP_ROOT / "domain").rglob("*.py"))
    assert files, "app/domain is empty"
    problems = _violations(files)
    assert not problems, "app.domain is not pure:\n  " + "\n  ".join(problems)


def test_the_check_actually_fails_on_a_violation(tmp_path: Path) -> None:
    """Negative control.

    A boundary test that cannot fail is not a boundary test. This writes a module
    with a forbidden import and asserts the walker catches it, so a refactor that
    accidentally neuters the AST walk is caught here rather than in production.
    """
    offender = BACKEND_ROOT / "app" / "rules" / "_boundary_probe_tmp.py"
    offender.write_text(
        textwrap.dedent(
            """
            import anthropic  # noqa: F401  -- deliberate violation, test fixture
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    try:
        problems = _violations([offender])
        assert problems, "the walker did not flag a direct `import anthropic`"
        assert any("anthropic" in p for p in problems)
    finally:
        offender.unlink()


def test_transitive_violation_is_caught() -> None:
    """Negative control for the transitive case specifically.

    The direct case is easy. This proves a violation reached through a permitted
    internal module is also caught -- the hole a naive implementation leaves.
    """
    middle = BACKEND_ROOT / "app" / "rules" / "_boundary_probe_mid_tmp.py"
    outer = BACKEND_ROOT / "app" / "rules" / "_boundary_probe_outer_tmp.py"
    middle.write_text("import httpx  # noqa: F401  -- test fixture\n", encoding="utf-8")
    outer.write_text(
        "from app.rules import _boundary_probe_mid_tmp  # noqa: F401\n", encoding="utf-8"
    )
    try:
        problems = _violations([outer])
        assert problems, "a violation one hop away was not caught"
        assert any("httpx" in p for p in problems)
    finally:
        middle.unlink()
        outer.unlink()


LLM_MODULE = APP_ROOT / "services" / "llm.py"


@pytest.mark.skipif(not LLM_MODULE.is_file(), reason="llm.py arrives in phase 4")
def test_llm_module_cannot_reach_the_engine() -> None:
    """The LLM module may read documents and write prose. Nothing else.

    It must not import either engine runner -- that is what would let a model's
    output stand in for a computed conclusion.
    """
    imports = _imports_of(LLM_MODULE)
    banned = ("app.rules", "app.argumentation")
    offenders = [i for i in imports if any(i == b or i.startswith(f"{b}.") for b in banned)]
    assert not offenders, f"app/services/llm.py imports the engine: {offenders}"


@pytest.mark.skipif(not LLM_MODULE.is_file(), reason="llm.py arrives in phase 4")
def test_llm_module_never_writes_conclusions() -> None:
    """``llm.py`` must not name the tables that store computed conclusions.

    A string match is coarse, but it is the right coarseness: there is no
    legitimate reason for the LLM module to mention these table names at all.
    """
    source = LLM_MODULE.read_text(encoding="utf-8")
    named = [t for t in CONCLUSION_TABLES if t in source]
    assert not named, (
        f"app/services/llm.py references conclusion table(s) {named}; "
        "the LLM must never write a route determination or an argument graph"
    )


def test_only_llm_service_imports_anthropic() -> None:
    """Exactly one module in the codebase may import the Anthropic SDK."""
    offenders: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        if path == LLM_MODULE:
            continue
        for imported in _imports_of(path):
            if imported == "anthropic" or imported.startswith("anthropic."):
                offenders.append(_module_name(path))
    assert not offenders, (
        "only app/services/llm.py may import anthropic; also imported by: "
        + ", ".join(sorted(set(offenders)))
    )


def test_the_engine_allow_list_has_not_quietly_grown() -> None:
    """Pins the allow-list, so widening it is a visible change in a diff.

    The boundary is only as strong as this list. An import added in passing --
    `requests` for "just fetching the rulebase", say -- would pass the purity
    test the moment someone added it here without thinking. Making the list
    itself an assertion forces the decision into review.
    """
    assert (
        frozenset(
            {
                "clingo",
                "clorm",
                "pydantic",
                "dateutil",
                "holidays",
                "yaml",
                "typing_extensions",
            }
        )
        == ALLOWED_THIRD_PARTY
    ), (
        "the engine's allow-list changed. If that is deliberate, update this test "
        "and record why in the comment above ALLOWED_THIRD_PARTY and in "
        "docs/ARCHITECTURE.md."
    )
