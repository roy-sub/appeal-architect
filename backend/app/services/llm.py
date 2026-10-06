"""The ONLY module in this codebase that imports the Anthropic SDK.

Three jobs, and nothing else:

1. **Transcribe** a scanned page or a phone photo into text.
2. **Extract** proposed facts from that text, as ``ExtractedFact`` with real
   character offsets, every one of them ``pending`` until a user confirms it.
3. **Write prose** — letter paragraphs from accepted argument nodes, and
   plain-language explanations of a single trace node.

It does not compute a route, a deadline, a required element, or whether an
argument holds. It has no import path to ``app.rules`` or
``app.argumentation``, and ``tests/test_boundary.py`` fails the build if one
appears. It never writes to ``route_determinations`` or ``argument_graphs``.

PHI discipline (docs/PRIVACY.md):
  * ``llm_calls`` records a **hash** of the prompt, never its content.
  * There is no ``case_id`` on that table, deliberately — linking a call to a
    case is a step towards linking it to a diagnosis.
  * Nothing here logs a prompt, a completion, a document, or a filename.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Literal

import anthropic

from app.config import get_settings
from app.problem import ErrorCode, Problem

logger = logging.getLogger("appeal_architect.llm")

Purpose = Literal["transcribe", "extract", "letter_prose", "explain"]

#: Fields the extractor may propose. Every one maps to a CaseFacts field, and
#: every one arrives as a proposal the user must confirm.
EXTRACTABLE_FIELDS: dict[str, str] = {
    "insurer_name": "The insurance company's name, as printed",
    "claim_number": "The claim or reference number, exactly as printed",
    "member_id_present": "Whether a member or subscriber ID appears on the letter",
    "denial_date": "The date printed on the letter, as YYYY-MM-DD",
    "service_date": "The date of service or treatment, as YYYY-MM-DD",
    "service_timing": "pre if the treatment has not happened yet, post if it has, "
    "concurrent if it is ongoing",
    "plan_type": "aca_marketplace, employer_fully_insured, employer_self_funded, "
    "medicare_advantage, medicaid, or unknown",
    "state": "The two-letter state code from the member's address",
    "denial_reasons": "One or more of: not_medically_necessary, prior_auth_missing, "
    "out_of_network, experimental_investigational, coding_error, "
    "not_covered_benefit, other",
    "cited_policy_language": "The exact sentence of plan or policy language the letter relies on",
    "claim_amount_usd": "The dollar amount in dispute, digits only",
}

EXTRACTION_TOOL: dict[str, Any] = {
    "name": "record_extracted_facts",
    "description": (
        "Record what the denial letter says. One entry per field you can find. "
        "Quote the exact source text for each so the user can check it."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string", "enum": list(EXTRACTABLE_FIELDS)},
                        "value": {
                            "type": "string",
                            "description": "The value as a string. For denial_reasons, "
                            "comma-separate several.",
                        },
                        "confidence": {
                            "type": "number",
                            "description": "0 to 1. Be honest: a blurry scan is low.",
                        },
                        "source_text": {
                            "type": "string",
                            "description": "The exact substring of the document this "
                            "came from, copied character for character so it can be "
                            "located in the text. Never paraphrase.",
                        },
                        "source_page": {"type": "integer"},
                    },
                    "required": [
                        "field",
                        "value",
                        "confidence",
                        "source_text",
                        "source_page",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["facts"],
        "additionalProperties": False,
    },
    "strict": True,
}

TRANSCRIBE_SYSTEM = """\
You transcribe scanned documents and photographs of documents into plain text.

Transcribe exactly what is on the page. Preserve line breaks and the reading
order. Do not correct spelling, do not expand abbreviations, do not summarise,
and do not add anything that is not printed on the page.

Where a word is genuinely illegible, write [illegible] in its place rather than
guessing. A guessed claim number or date is worse than a gap, because somebody
will rely on it.

Output the transcription and nothing else. No preamble, no commentary."""

EXTRACT_SYSTEM = """\
You read health-insurance denial letters and record what they say.

You are reading on behalf of someone who is going to appeal this denial. What
you record becomes a list of proposals they will confirm or correct one by one,
with your quoted source text shown next to each. You are not deciding anything.

Rules:

1. Record only what the document states. If the letter does not say what kind of
   plan this is, do not infer it from the insurer's name. Omit the field.
2. `source_text` must be an exact substring of the document, copied character for
   character. It is used to locate and highlight the passage. A paraphrase breaks
   that, so never paraphrase.
3. Be honest about confidence. A blurry scan, a handwritten note, or an ambiguous
   phrase is low confidence. Overconfidence here costs the user time they may not
   have.
4. Never state or imply a deadline, an appeal route, a review level, or whether
   the denial is likely to be overturned. Those are computed elsewhere from the
   facts the user confirms. If the letter itself prints a deadline, do not record
   it as a fact — the engine computes deadlines from the regulations.
5. If a field appears more than once with different values, record the one the
   letter presents as authoritative and lower your confidence."""

LETTER_SYSTEM = """\
You write the body paragraphs of a health-insurance appeal letter.

You are given argument nodes the user has accepted, their premises, their
citations, and the facts the user has confirmed. Write one paragraph per
argument, in the order given.

Absolute rules:

1. **Introduce no factual claim that is not in the input.** No dates, no amounts,
   no diagnoses, no policy language, no clinical assertions beyond what you were
   given. If an argument's premise is thin, write it thin.
2. **Never predict an outcome.** Do not write that the denial will be overturned,
   that the law is clearly on the member's side, or that the insurer has no
   choice. State the argument and its support.
3. **Plain, specific, steady.** Grade-8 reading level. Active voice. No
   exclamation marks. No war metaphors, no "fight", no "demand". This is a letter
   a reviewer will read, and a reviewer responds to precision.
4. One paragraph per argument node, each tagged with the node id you were given.
5. Quote plan or policy language only where it was supplied to you, and quote it
   exactly.

Return a JSON array. Each element: {"argument_node_id": "...", "text": "..."}.
Return the array and nothing else."""

EXPLAIN_SYSTEM = """\
You explain one step of a procedural or logical conclusion in plain language.

You are given a conclusion, the rule that produced it, and the premises it rests
on. Rewrite that in two or three sentences someone reads at a grade-8 level while
stressed and tired.

Do not add a conclusion that was not given to you. Do not say what the person
should do. Do not predict an outcome. Do not soften a deadline or round a date.
If the input says a date is uncertain, say it is uncertain."""


@dataclass
class LLMResult:
    """What a call returned, plus the metadata that gets logged. No PHI."""

    content: Any
    purpose: Purpose
    model: str
    prompt_hash: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def _prompt_hash(*parts: str) -> str:
    """A digest of the prompt, so usage can be audited without storing content."""
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def _client() -> anthropic.Anthropic:
    settings = get_settings()
    if not settings.anthropic_configured:
        raise Problem(
            503,
            ErrorCode.SERVICE_NOT_CONFIGURED,
            "Reading documents is not set up on this server. Set ANTHROPIC_API_KEY and restart.",
            extra={"service": "Anthropic", "missing_env": ["ANTHROPIC_API_KEY"]},
        )
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _log(result: LLMResult, user_id: str | None) -> None:
    """Record the call. Hash only -- never the prompt, never the completion."""
    logger.info(
        "llm call purpose=%s model=%s prompt_sha256=%s in=%d out=%d ms=%d",
        result.purpose,
        result.model,
        result.prompt_hash[:16],
        result.input_tokens,
        result.output_tokens,
        result.latency_ms,
    )
    if user_id is None:
        return
    try:
        from app.db.client import get_client

        get_client().table("llm_calls").insert(
            {
                "user_id": user_id,
                "purpose": result.purpose,
                "model": result.model,
                "prompt_hash": result.prompt_hash,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "latency_ms": result.latency_ms,
            }
        ).execute()
    except Exception:
        logger.warning("could not record llm usage", exc_info=False)


def check_monthly_cap(user_id: str) -> None:
    """Enforce the per-user monthly cap *before* the call is made.

    A cap checked afterwards is not a cap.
    """
    settings = get_settings()
    if not settings.supabase_configured:
        return
    from datetime import UTC, datetime

    from app.db.client import get_client

    start_of_month = datetime.now(tz=UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = (
        get_client()
        .table("llm_calls")
        .select("id")
        .eq("user_id", user_id)
        .gte("created_at", start_of_month.isoformat())
        .execute()
    )
    used = len(result.data) if isinstance(result.data, list) else 0
    if used >= settings.llm_monthly_call_cap:
        raise Problem(
            429,
            ErrorCode.LLM_CAP_REACHED,
            f"You have reached this month's limit of {settings.llm_monthly_call_cap} "
            "document readings. It resets on the first of the month. Your cases and "
            "documents are untouched.",
            extra={"used": used, "cap": settings.llm_monthly_call_cap},
        )


def _call(
    *,
    purpose: Purpose,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | None = None,
    user_id: str | None = None,
    hash_parts: tuple[str, ...] = (),
) -> LLMResult:
    settings = get_settings()
    client = _client()

    kwargs: dict[str, Any] = {
        "model": settings.anthropic_model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
        # Extraction must be reproducible: the same scan should propose the same
        # facts twice, or a user who refreshes sees a different letter.
        "temperature": 0,
    }
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice

    started = time.monotonic()
    try:
        response = client.messages.create(**kwargs)
    except anthropic.RateLimitError:
        raise Problem(
            429,
            ErrorCode.RATE_LIMITED,
            "The document reader is busy. Try again in a minute — nothing was lost.",
        ) from None
    except anthropic.APIStatusError as error:
        logger.error("anthropic api error status=%s", error.status_code)
        raise Problem(
            502,
            ErrorCode.INTERNAL_ERROR,
            "We could not read the document just now. Try again, and if it keeps "
            "happening you can type the details in by hand instead.",
        ) from None
    except anthropic.APIConnectionError:
        raise Problem(
            502,
            ErrorCode.INTERNAL_ERROR,
            "We could not reach the document reader. Check back shortly.",
        ) from None

    latency_ms = int((time.monotonic() - started) * 1000)
    result = LLMResult(
        content=response.content,
        purpose=purpose,
        model=response.model,
        prompt_hash=_prompt_hash(system, *hash_parts),
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=latency_ms,
    )
    _log(result, user_id)
    return result


# ---------------------------------------------------------------------------
# 1. Transcription
# ---------------------------------------------------------------------------

#: Media types accepted for transcription.
IMAGE_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


def transcribe_image(
    image_bytes: bytes, media_type: str, *, user_id: str | None = None
) -> tuple[str, LLMResult]:
    """Transcribe one scanned page or photograph into plain text.

    This replaces the Tesseract OCR path the build spec specifies. Tesseract
    cannot be installed on the target host -- Render's native Python runtime has
    no apt -- and the model reads phone photographs of creased letters markedly
    better in any case. Reading a document is the LLM's sanctioned job, so this
    stays inside the boundary: it produces text, never a conclusion.

    The transcription becomes the document's stored text, so the character
    offsets a fact's source span points at are offsets into real characters the
    user can see highlighted.
    """
    if media_type not in IMAGE_MEDIA_TYPES:
        raise Problem(
            422,
            ErrorCode.VALIDATION_FAILED,
            f"We cannot read {media_type} images. Use a PDF, a PNG or a JPEG.",
        )

    encoded = base64.standard_b64encode(image_bytes).decode("ascii")
    result = _call(
        purpose="transcribe",
        system=TRANSCRIBE_SYSTEM,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded,
                        },
                    },
                    {"type": "text", "text": "Transcribe this page."},
                ],
            }
        ],
        user_id=user_id,
        # The image is hashed by its own digest, not its content, so the prompt
        # hash identifies the call without storing anything of the document.
        hash_parts=(hashlib.sha256(image_bytes).hexdigest(),),
    )

    text = "".join(block.text for block in result.content if getattr(block, "type", "") == "text")
    return text.strip(), result


# ---------------------------------------------------------------------------
# 2. Extraction
# ---------------------------------------------------------------------------


@dataclass
class RawExtraction:
    """One proposal, before it is turned into an ExtractedFact.

    ``source_text`` is located in the document by the ingestion service, which
    is what produces the real character offsets.
    """

    field: str
    value: str
    confidence: float
    source_text: str
    source_page: int


def extract_facts(
    document_text: str, *, user_id: str | None = None
) -> tuple[list[RawExtraction], LLMResult]:
    """Propose facts from a document's text.

    Everything returned is a **proposal**. The caller turns each into an
    ``ExtractedFact`` with ``status=pending``, and no value reaches the rules
    engine until a user has confirmed or corrected it.
    """
    result = _call(
        purpose="extract",
        system=EXTRACT_SYSTEM,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": (
                    "Here is the text of a denial letter. Record what it says.\n\n"
                    "<document>\n" + document_text + "\n</document>"
                ),
            }
        ],
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": EXTRACTION_TOOL["name"]},
        user_id=user_id,
        hash_parts=(hashlib.sha256(document_text.encode("utf-8")).hexdigest(),),
    )

    proposals: list[RawExtraction] = []
    for block in result.content:
        if getattr(block, "type", "") != "tool_use":
            continue
        payload = block.input
        if not isinstance(payload, dict):
            continue
        for item in payload.get("facts", []):
            if not isinstance(item, dict):
                continue
            field = item.get("field")
            if field not in EXTRACTABLE_FIELDS:
                # A field outside the schema is dropped rather than stored. It
                # could not be mapped onto CaseFacts anyway.
                continue
            try:
                confidence = float(item.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            proposals.append(
                RawExtraction(
                    field=field,
                    value=str(item.get("value", "")),
                    confidence=min(max(confidence, 0.0), 1.0),
                    source_text=str(item.get("source_text", "")),
                    source_page=max(int(item.get("source_page", 1) or 1), 1),
                )
            )

    return proposals, result


# ---------------------------------------------------------------------------
# 3. Prose
# ---------------------------------------------------------------------------


def write_letter_paragraphs(
    *,
    arguments: list[dict[str, Any]],
    confirmed_facts: dict[str, Any],
    user_id: str | None = None,
) -> tuple[list[dict[str, str]], LLMResult]:
    """Write one paragraph per accepted argument node.

    The model receives only the accepted nodes, their premises, their citations
    and the user's confirmed facts. Its system prompt forbids introducing any
    factual claim not present in that input, and the caller re-checks every
    paragraph afterwards: untagged prose is dropped rather than printed.
    """
    payload = json.dumps(
        {"arguments": arguments, "confirmed_facts": confirmed_facts},
        sort_keys=True,
        default=str,
    )
    result = _call(
        purpose="letter_prose",
        system=LETTER_SYSTEM,
        max_tokens=8000,
        messages=[
            {
                "role": "user",
                "content": (
                    "Write the body paragraphs for this appeal. Use only what is "
                    "here.\n\n" + payload
                ),
            }
        ],
        user_id=user_id,
        hash_parts=(hashlib.sha256(payload.encode("utf-8")).hexdigest(),),
    )

    text = "".join(
        block.text for block in result.content if getattr(block, "type", "") == "text"
    ).strip()

    # The model was asked for a JSON array. Be forgiving about fencing, strict
    # about shape: anything unparseable yields no paragraphs rather than prose
    # the caller cannot attribute to an argument.
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("letter prose was not valid JSON; dropping it")
        return [], result

    paragraphs: list[dict[str, str]] = []
    if isinstance(parsed, list):
        for item in parsed:
            if (
                isinstance(item, dict)
                and isinstance(item.get("argument_node_id"), str)
                and isinstance(item.get("text"), str)
                and item["text"].strip()
            ):
                paragraphs.append(
                    {
                        "argument_node_id": item["argument_node_id"],
                        "text": item["text"].strip(),
                    }
                )
    return paragraphs, result


def explain_trace_node(
    *,
    conclusion: str,
    rule_id: str,
    premises: list[str],
    citation: str | None = None,
    user_id: str | None = None,
) -> tuple[str, LLMResult]:
    """Rewrite one computed conclusion in plain language.

    The conclusion is handed to the model already computed. The model rewrites
    it; it does not derive it.
    """
    payload = json.dumps(
        {
            "conclusion": conclusion,
            "rule": rule_id,
            "premises": premises,
            "citation": citation,
        },
        sort_keys=True,
    )
    result = _call(
        purpose="explain",
        system=EXPLAIN_SYSTEM,
        max_tokens=600,
        messages=[{"role": "user", "content": payload}],
        user_id=user_id,
        hash_parts=(hashlib.sha256(payload.encode("utf-8")).hexdigest(),),
    )
    text = "".join(block.text for block in result.content if getattr(block, "type", "") == "text")
    return text.strip(), result
