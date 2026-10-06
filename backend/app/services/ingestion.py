"""Documents in, per-page text and proposed facts out.

The order matters:

1. **A PDF's own text layer**, via ``pypdfium2``. Free, exact, and the common
   case for a letter printed to PDF from the insurer's system.
2. **Transcription by the model**, for a page with no text layer and for photos
   taken on a phone.

Character offsets are preserved throughout, so a proposed fact's
``source_span`` points at real characters the user can see highlighted in the
document viewer. That is the whole trust model: nobody should confirm a fact
they cannot check against the page.

### Why there is no Tesseract here

The build spec specifies ``pytesseract`` as the OCR fallback. It is not used,
for two reasons.

The practical one: the Tesseract binary cannot be installed on the target host.
Render's native Python runtime has no ``apt``, and we are not using Docker.

The better one: a photograph of a creased denial letter taken on a phone in a
waiting room is exactly the input Tesseract is worst at and a vision model is
good at. Reading a document is the LLM's sanctioned job under this
architecture — it produces text, never a conclusion — so the fallback stays
inside the boundary.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field

from app.domain.case import ExtractedFact, FactStatus, SourceSpan
from app.problem import ErrorCode, Problem
from app.services import llm

logger = logging.getLogger("appeal_architect.ingestion")

#: Pages with fewer than this many characters of text layer are treated as
#: scans. A page that is genuinely nearly blank costs one transcription call;
#: a scan mistaken for text costs the user a document we cannot read.
MIN_TEXT_LAYER_CHARS = 40

#: Pages per document. Past this the upload is refused rather than silently
#: truncated -- a letter is a few pages, and a 200-page plan document would
#: exhaust the monthly LLM cap in one upload.
MAX_PAGES = 30

#: Render at this scale before transcription. 2x gives the model enough detail
#: on small print without making the request enormous.
RENDER_SCALE = 2.0

ACCEPTED_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


@dataclass
class Page:
    """One page of a document, and where its text starts in the whole."""

    number: int
    text: str
    #: Offset of this page's text within the document's full text.
    offset: int
    transcribed: bool = False


@dataclass
class IngestedDocument:
    """A document, read."""

    pages: list[Page] = field(default_factory=list)
    #: Every page's text joined with form feeds, which is what gets stored and
    #: what source spans index into.
    full_text: str = ""
    used_transcription: bool = False

    @property
    def page_count(self) -> int:
        return len(self.pages)


PAGE_SEPARATOR = "\n\f\n"


def _assemble(pages: list[Page]) -> IngestedDocument:
    """Join pages, recording each one's offset into the joined text."""
    parts: list[str] = []
    cursor = 0
    for page in pages:
        page.offset = cursor
        parts.append(page.text)
        cursor += len(page.text) + len(PAGE_SEPARATOR)
    return IngestedDocument(
        pages=pages,
        full_text=PAGE_SEPARATOR.join(parts),
        used_transcription=any(p.transcribed for p in pages),
    )


def read_pdf(data: bytes, *, user_id: str | None = None) -> IngestedDocument:
    """Read a PDF: text layer where there is one, transcription where there is not."""
    import pypdfium2

    try:
        document = pypdfium2.PdfDocument(io.BytesIO(data))
    except Exception:
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            "We could not open that PDF. If it is password-protected, remove the "
            "password and upload it again.",
        ) from None

    count = len(document)
    if count == 0:
        raise Problem(422, ErrorCode.VALIDATION_FAILED, "That PDF has no pages in it.")
    if count > MAX_PAGES:
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            f"That document has {count} pages and we read up to {MAX_PAGES}. Upload "
            "just the denial letter, and add the plan document separately.",
            extra={"page_count": count, "max_pages": MAX_PAGES},
        )

    pages: list[Page] = []
    for index in range(count):
        pdf_page = document[index]
        layer = pdf_page.get_textpage().get_text_range() or ""
        normalised = _normalise(layer)

        if len(normalised.strip()) >= MIN_TEXT_LAYER_CHARS:
            pages.append(Page(number=index + 1, text=normalised, offset=0))
            continue

        # No usable text layer: rasterise and transcribe.
        logger.info("page %d has no text layer; transcribing", index + 1)
        bitmap = pdf_page.render(scale=RENDER_SCALE)
        image = bitmap.to_pil()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        text, _ = llm.transcribe_image(buffer.getvalue(), "image/png", user_id=user_id)
        pages.append(Page(number=index + 1, text=_normalise(text), offset=0, transcribed=True))

    return _assemble(pages)


def read_image(data: bytes, mime: str, *, user_id: str | None = None) -> IngestedDocument:
    """Read a photograph or a scan: straight to transcription."""
    text, _ = llm.transcribe_image(data, mime, user_id=user_id)
    page = Page(number=1, text=_normalise(text), offset=0, transcribed=True)
    return _assemble([page])


def read_document(data: bytes, mime: str, *, user_id: str | None = None) -> IngestedDocument:
    """Read any accepted document."""
    if mime not in ACCEPTED_MIME:
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            "We read PDFs and photographs. Upload a PDF, or take a photo of each page.",
            extra={"accepted": sorted(ACCEPTED_MIME)},
        )
    if not data:
        raise Problem(422, ErrorCode.VALIDATION_FAILED, "That file is empty.")
    if mime == "application/pdf":
        return read_pdf(data, user_id=user_id)
    return read_image(data, mime, user_id=user_id)


def _normalise(text: str) -> str:
    """Tidy whitespace without moving any character the user will see.

    Only trailing spaces and runs of blank lines are touched. Nothing is
    inserted or deleted mid-line, because every offset downstream is an offset
    into this string.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ---------------------------------------------------------------------------
# Locating a quoted span in the document
# ---------------------------------------------------------------------------


def _collapse(text: str) -> tuple[str, list[int]]:
    """Whitespace-collapsed text, plus a map back to original offsets.

    The model quotes source text faithfully but can normalise whitespace --
    a line break in the letter becomes a space in the quote. Matching on
    collapsed text and mapping back gives offsets into the real characters.
    """
    out: list[str] = []
    index: list[int] = []
    previous_space = False
    for position, char in enumerate(text):
        if char.isspace():
            if previous_space:
                continue
            out.append(" ")
            index.append(position)
            previous_space = True
        else:
            out.append(char)
            index.append(position)
            previous_space = False
    return "".join(out), index


def locate_span(document_text: str, quote: str) -> tuple[int, int] | None:
    """Find ``quote`` in ``document_text``, returning real character offsets.

    Tries an exact match first, then a whitespace-insensitive one, then a
    case-insensitive one. Returns None rather than guessing: a span that points
    at the wrong characters is worse than no highlight, because the user would
    confirm a fact against text that does not support it.
    """
    quote = quote.strip()
    if not quote:
        return None

    exact = document_text.find(quote)
    if exact != -1:
        return exact, exact + len(quote)

    haystack, mapping = _collapse(document_text)
    needle, _ = _collapse(quote)
    needle = needle.strip()
    if not needle:
        return None

    found = haystack.find(needle)
    if found == -1:
        found = haystack.lower().find(needle.lower())
    if found == -1:
        return None

    start = mapping[found]
    end_index = min(found + len(needle) - 1, len(mapping) - 1)
    return start, mapping[end_index] + 1


def _page_for_offset(document: IngestedDocument, offset: int) -> int:
    """Which page a document offset falls on."""
    page_number = 1
    for page in document.pages:
        if offset >= page.offset:
            page_number = page.number
        else:
            break
    return page_number


def propose_facts(document: IngestedDocument, *, user_id: str | None = None) -> list[ExtractedFact]:
    """Read the document and return proposals, every one ``pending``.

    The source span is located in the stored text, so clicking a fact scrolls to
    and highlights the characters it actually came from. A proposal whose quote
    cannot be located keeps its value but carries no span, and the UI says so —
    "we could not find this on the page" is a reason to look twice, not a reason
    to hide the proposal.
    """
    if not document.full_text.strip():
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            "We could not get any text out of that document. If it is a photo, try "
            "again in better light with the whole page in frame.",
        )

    proposals, _ = llm.extract_facts(document.full_text, user_id=user_id)

    facts: list[ExtractedFact] = []
    for proposal in proposals:
        span: SourceSpan | None = None
        located = locate_span(document.full_text, proposal.source_text)
        if located is not None:
            start, end = located
            span = SourceSpan(page=_page_for_offset(document, start), start=start, end=end)
        else:
            logger.info("could not locate the quoted span for field %s", proposal.field)

        facts.append(
            ExtractedFact(
                field=proposal.field,
                value=proposal.value,
                # A proposal we cannot show the user the source of is inherently
                # less trustworthy, so its confidence is capped. They will see
                # it flagged as needing a closer look.
                confidence=proposal.confidence if span else min(proposal.confidence, 0.5),
                source_span=span,
                status=FactStatus.PENDING,
            )
        )

    return facts
