"""Letter assembly, the paragraph check, and rendering.

The §4.4 gate: a paragraph is valid iff it carries an ``argument_node_id`` or
the reserved ``procedural`` tag. Untagged model prose is dropped, because that
is exactly what would put an unsupported factual claim into a legal filing.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.argument import Argument, ArgumentGraph
from app.domain.case import CaseFacts, DenialReason, PlanType, ServiceTiming
from app.rules.runner import determine_route
from app.services.letters import (
    PROCEDURAL,
    Paragraph,
    _accepted_arguments,
    _closing,
    _opening,
    check_paragraphs,
    render_docx,
    render_html,
)
from app.site import DISCLAIMER


def facts(**overrides) -> CaseFacts:
    base = {
        "plan_type": PlanType.ACA_MARKETPLACE,
        "state": "CA",
        "insurer_name": "Anthem Blue Cross",
        "member_id_present": True,
        "claim_number": "CLM-4471902",
        "denial_date": date(2026, 9, 14),
        "service_timing": ServiceTiming.POST_SERVICE,
        "denial_reasons": [DenialReason.NOT_MEDICALLY_NECESSARY],
        "filer": "member",
    }
    return CaseFacts(**{**base, **overrides})


# ---- the §4.4 gate ---------------------------------------------------------


def test_untagged_generated_prose_is_dropped() -> None:
    """The gate. A paragraph we cannot attribute does not go in the letter."""
    kept = check_paragraphs(
        [
            Paragraph(text="Procedural header", source="procedural"),
            Paragraph(text="Tagged argument", source="argument", argument_node_id="mn.x"),
            Paragraph(text="Model invented this", source="argument", argument_node_id=None),
        ]
    )
    assert [p.text for p in kept] == ["Procedural header", "Tagged argument"]


def test_procedural_paragraphs_survive_the_gate() -> None:
    """Read literally, §4.4 would delete the letter's legally necessary header.

    The design already specifies a `procedural` badge for paragraphs no argument
    produced, so the gate accepts that tag -- and those paragraphs come from a
    fixed template, never from model prose.
    """
    kept = check_paragraphs([Paragraph(text="Appeal rights", source="procedural")])
    assert len(kept) == 1
    assert kept[0].to_dict()["argument_node_id"] == PROCEDURAL


def test_every_paragraph_in_the_letter_is_attributable() -> None:
    route = determine_route(facts())
    paragraphs = check_paragraphs([*_opening(facts(), route), *_closing(facts(), route)])
    assert paragraphs
    for paragraph in paragraphs:
        tag = paragraph.to_dict()["argument_node_id"]
        assert tag, "a paragraph with no tag reached the letter"


# ---- the procedural header -------------------------------------------------


def test_the_opening_identifies_the_claim_and_cites_the_appeal_right() -> None:
    route = determine_route(facts())
    text = " ".join(p.text for p in _opening(facts(), route))
    assert "CLM-4471902" in text
    assert "14 September 2026" in text
    assert "45 CFR 147.136" in text
    assert "13 March 2027" in text


def test_the_opening_discloses_an_ambiguous_deadline() -> None:
    """The letter says how the date was counted, so the insurer can disagree in
    writing rather than silently."""
    route = determine_route(facts())
    text = " ".join(p.text for p in _opening(facts(), route))
    assert "date printed on your letter" in text


def test_the_opening_requests_the_claim_file() -> None:
    """29 CFR 2560.503-1(h). Often where the argument actually is."""
    route = determine_route(facts())
    text = " ".join(p.text for p in _opening(facts(), route))
    assert "2560.503-1" in text
    assert "free copies" in text


def test_the_closing_states_the_insurers_own_deadline() -> None:
    route = determine_route(facts())
    text = " ".join(p.text for p in _closing(facts(), route))
    assert "13 November 2026" in text
    assert "external review" in text


def test_no_outcome_language_anywhere_in_the_template() -> None:
    """The product never implies a result. A letter that did would be both a
    lie and worse advocacy."""
    route = determine_route(facts())
    text = " ".join(p.text for p in [*_opening(facts(), route), *_closing(facts(), route)])
    lowered = text.lower()
    for banned in (
        "guaranteed",
        "we'll win",
        "will be overturned",
        "you will win",
        "fight back",
        "loophole",
        "no choice",
    ):
        assert banned not in lowered, f"the letter template uses outcome language: {banned}"
    assert "!" not in text


# ---- argument ordering -----------------------------------------------------


def test_solid_ground_arguments_come_before_worth_adding() -> None:
    """The order is the argument: a reviewer reads the strongest point first."""
    graph = ArgumentGraph(
        schemes_version="1.0.0",
        arguments=[
            Argument(id="a1", side="patient", claim="Solid one"),
            Argument(id="b1", side="patient", claim="Contestable one"),
        ],
        grounded_extension=["a1"],
        worth_adding=["b1"],
    )
    ordered = _accepted_arguments(graph)
    assert [item["argument_node_id"] for item in ordered] == ["a1", "b1"]
    assert ordered[0]["tier"] == "Solid ground"
    assert ordered[1]["tier"] == "Worth adding"


def test_defeated_arguments_are_not_sent() -> None:
    """An argument the solver found does not hold has no place in a filing."""
    graph = ArgumentGraph(
        schemes_version="1.0.0",
        arguments=[Argument(id="c1", side="patient", claim="Does not hold")],
        defeated=["c1"],
    )
    assert _accepted_arguments(graph) == []


# ---- rendering -------------------------------------------------------------


def _letter() -> dict:
    return {
        "version": 1,
        "body": {
            "paragraphs": [
                {"text": "First paragraph.", "argument_node_id": PROCEDURAL},
                {
                    "text": "Second one, from an argument.",
                    "argument_node_id": "mn.plan_own_criteria",
                },
            ],
            "disclaimer": DISCLAIMER,
        },
    }


def _case() -> dict:
    return {"insurer_name": "Anthem Blue Cross", "claim_number": "CLM-4471902"}


def test_html_renders_for_us_letter_with_one_inch_margins() -> None:
    html = render_html(_letter(), _case())
    assert "size: Letter" in html
    assert "margin: 1in" in html
    assert "First paragraph." in html
    assert DISCLAIMER in html, "the disclaimer appears in every generated letter"


def test_html_carries_no_node_badges() -> None:
    """Badges are an editing affordance, not part of the filed document."""
    html = render_html(_letter(), _case())
    assert "mn.plan_own_criteria" not in html


def test_html_escapes_user_supplied_text() -> None:
    letter = _letter()
    letter["body"]["paragraphs"][0]["text"] = "<script>alert(1)</script>"
    html = render_html(letter, {"insurer_name": "<b>Evil</b>", "claim_number": "x"})
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>Evil</b>" not in html


def test_pdf_renders() -> None:
    from app.services.letters import render_pdf

    data = render_pdf(render_html(_letter(), _case()))
    assert data.startswith(b"%PDF"), "that is not a PDF"
    assert len(data) > 1000


def test_docx_renders() -> None:
    data = render_docx(_letter(), _case())
    # A .docx is a zip archive.
    assert data[:2] == b"PK"
    assert len(data) > 1000


def test_docx_contains_the_disclaimer() -> None:
    import io
    import zipfile

    data = render_docx(_letter(), _case())
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "prepares documents and explains procedure" in document


@pytest.mark.parametrize("fmt", ["txt", "rtf", "", "PDF "])
def test_an_unknown_export_format_is_refused(fmt: str) -> None:
    from app.problem import Problem
    from app.services import letters as letters_service

    with pytest.raises(Problem, match="pdf or docx"):
        letters_service.export("case", "letter", "user", fmt)
