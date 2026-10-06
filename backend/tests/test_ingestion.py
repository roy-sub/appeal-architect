"""Document reading, and the span location the trust model depends on.

A source span that points at the wrong characters is worse than no highlight:
the user would confirm a fact against text that does not support it. So
``locate_span`` returns None rather than guessing, and that is asserted here.
"""

from __future__ import annotations

import pytest

from app.services.ingestion import (
    MAX_PAGES,
    PAGE_SEPARATOR,
    IngestedDocument,
    Page,
    _assemble,
    _normalise,
    _page_for_offset,
    locate_span,
)

LETTER = """Anthem Blue Cross
PO Box 60007, Los Angeles CA 90060

14 September 2026

Dear Ms Rivera,

We have completed our review of claim CLM-4471902 for services
provided on 2 September 2026.

We have determined that the requested service is not medically
necessary as defined in your plan documents.

You have the right to appeal this decision.

Sincerely,
Utilization Management"""


def test_exact_quote_is_located() -> None:
    span = locate_span(LETTER, "CLM-4471902")
    assert span is not None
    start, end = span
    assert LETTER[start:end] == "CLM-4471902"


def test_a_quote_spanning_a_line_break_is_located() -> None:
    """The model quotes faithfully but normalises whitespace: a line break in
    the letter becomes a space in the quote. The offsets must still land on the
    real characters."""
    span = locate_span(LETTER, "not medically necessary as defined in your plan documents")
    assert span is not None
    start, end = span
    matched = LETTER[start:end]
    assert "not medically" in matched
    assert "plan documents" in matched
    assert "\n" in matched, "the matched region should cross the real line break"


def test_a_quote_with_collapsed_double_spaces_is_located() -> None:
    document = "The   service    was denied."
    span = locate_span(document, "The service was denied.")
    assert span is not None
    start, end = span
    assert document[start:end].replace("   ", " ").replace("    ", " ")


def test_case_differences_are_tolerated() -> None:
    span = locate_span(LETTER, "DEAR MS RIVERA")
    assert span is not None


def test_a_quote_that_is_not_there_returns_none() -> None:
    """Returns None rather than a near miss.

    A span pointing at the wrong sentence would have the user confirm a fact
    against text that does not support it, which is worse than no highlight.
    """
    assert locate_span(LETTER, "we approve this claim in full") is None


def test_an_empty_quote_returns_none() -> None:
    assert locate_span(LETTER, "") is None
    assert locate_span(LETTER, "   ") is None


def test_normalise_does_not_move_characters_within_a_line() -> None:
    """Every offset downstream indexes into the normalised text, so normalising
    must not insert or delete anything mid-line."""
    source = "Claim  CLM-123   \n\n\n\nNext line\n"
    out = _normalise(source)
    assert "Claim  CLM-123" in out, "interior spacing is preserved"
    assert "\n\n\n" not in out, "runs of blank lines are collapsed"
    assert not out.endswith("\n")


def test_page_offsets_map_back_to_the_right_page() -> None:
    document = _assemble(
        [
            Page(number=1, text="page one text", offset=0),
            Page(number=2, text="page two text", offset=0),
            Page(number=3, text="page three text", offset=0),
        ]
    )
    assert document.page_count == 3
    assert document.full_text.count(PAGE_SEPARATOR) == 2

    two = document.full_text.index("page two")
    three = document.full_text.index("page three")
    assert _page_for_offset(document, 0) == 1
    assert _page_for_offset(document, two) == 2
    assert _page_for_offset(document, three) == 3


def test_a_span_found_in_the_joined_text_resolves_to_its_page() -> None:
    document = _assemble(
        [
            Page(number=1, text="Dear Ms Rivera", offset=0),
            Page(number=2, text="Claim CLM-4471902 was denied", offset=0),
        ]
    )
    span = locate_span(document.full_text, "CLM-4471902")
    assert span is not None
    assert _page_for_offset(document, span[0]) == 2


def test_an_empty_document_has_no_text() -> None:
    document = IngestedDocument()
    assert document.page_count == 0
    assert document.full_text == ""


def test_the_page_ceiling_is_a_real_number() -> None:
    """A 200-page plan document would exhaust the monthly LLM cap in one upload,
    so it is refused rather than silently truncated."""
    assert 5 <= MAX_PAGES <= 50


@pytest.mark.parametrize("mime", ["application/pdf", "image/png", "image/jpeg", "image/webp"])
def test_accepted_mime_types(mime: str) -> None:
    from app.services.ingestion import ACCEPTED_MIME

    assert mime in ACCEPTED_MIME


def test_an_unsupported_file_type_is_refused() -> None:
    from app.problem import Problem
    from app.services.ingestion import read_document

    with pytest.raises(Problem) as caught:
        read_document(b"x", "application/zip")
    assert caught.value.status_code == 422
    assert "PDF" in caught.value.detail


def test_an_empty_file_is_refused() -> None:
    from app.problem import Problem
    from app.services.ingestion import read_document

    with pytest.raises(Problem, match="empty"):
        read_document(b"", "application/pdf")


def test_a_corrupt_pdf_is_refused_with_an_actionable_message() -> None:
    from app.problem import Problem
    from app.services.ingestion import read_pdf

    with pytest.raises(Problem) as caught:
        read_pdf(b"this is not a pdf at all")
    assert caught.value.status_code == 422
    assert "password" in caught.value.detail.lower()
