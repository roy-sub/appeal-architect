"""The CLI runner, so the engine stays auditable without the app."""

from __future__ import annotations

import json

import pytest

from app.rules.cli import main


def test_cli_prints_a_route(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "--plan",
            "aca_marketplace",
            "--state",
            "CA",
            "--denial-date",
            "2026-09-14",
            "--timing",
            "post",
            "--reason",
            "not_medically_necessary",
            "--trace",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "13 March 2027" in out
    assert "Internal appeal" in out
    assert "fed.internal_appeal.window" in out
    assert "UNVERIFIED" in out


def test_cli_json_output_is_a_full_determination(capsys: pytest.CaptureFixture[str]) -> None:
    main(
        [
            "--plan",
            "aca_marketplace",
            "--state",
            "NY",
            "--denial-date",
            "2026-09-14",
            "--timing",
            "pre",
            "--reason",
            "prior_auth_missing",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["rulebase_version"]
    assert payload["trace"] and payload["deadlines"]
    assert any(d["id"] == "internal_appeal" for d in payload["deadlines"])


def test_cli_refuses_to_guess_an_unsupported_plan(capsys: pytest.CaptureFixture[str]) -> None:
    main(
        [
            "--plan",
            "medicaid",
            "--state",
            "TX",
            "--denial-date",
            "2026-09-14",
            "--timing",
            "post",
            "--reason",
            "other",
        ]
    )
    out = capsys.readouterr().out
    assert "No route" in out
    assert "we do not guess" in out
