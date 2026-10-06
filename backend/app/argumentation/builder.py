"""Confirmed facts + schemes → an argumentation framework.

PURE: no network, no LLM, no database.

The insurer's stated reason becomes an argument. Each scheme that matches that
reason becomes a counter-argument attacking it. Each of that scheme's known
rebuttals becomes a further argument attacking the counter-argument — so the
solver genuinely computes defeat rather than the application asserting it.

A rebuttal is itself attacked by the evidence that answers it, when the user has
that evidence. That is the whole mechanism: attaching a policy version page is
what moves an argument from "Worth adding" to "Solid ground", and the solver,
not this module, is what notices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.domain.argument import Argument, Attack, Premise
from app.domain.case import CaseFacts, DenialReason
from app.domain.trace import Citation

SCHEMES_DIR = Path(__file__).resolve().parent / "schemes"

#: Prefix for the generated argument representing the insurer's own reason.
INSURER_PREFIX = "insurer."

#: How each denial reason is phrased as the insurer's assertion. Written out
#: rather than derived, so the user reads a sentence and not an enum.
INSURER_CLAIMS: dict[DenialReason, str] = {
    DenialReason.NOT_MEDICALLY_NECESSARY: (
        "The insurer says the service is not medically necessary as the plan defines it."
    ),
    DenialReason.PRIOR_AUTH_MISSING: (
        "The insurer says the required prior authorisation was not obtained."
    ),
    DenialReason.OUT_OF_NETWORK: ("The insurer says the provider was outside the plan's network."),
    DenialReason.EXPERIMENTAL: (
        "The insurer says the treatment is experimental or investigational and therefore excluded."
    ),
    DenialReason.CODING_ERROR: ("The insurer says the claim was coded or submitted incorrectly."),
    DenialReason.NOT_COVERED_BENEFIT: ("The insurer says this is not a benefit the plan covers."),
    DenialReason.OTHER: ("The insurer gave a reason that does not fit the usual categories."),
}


class SchemeError(ValueError):
    """A scheme file the builder will not load."""


@dataclass
class Scheme:
    """One loaded scheme file."""

    id: str
    denial_reason: str
    side: str
    claim_template: str
    premises: list[dict[str, str]]
    attacks: list[dict[str, str]]
    known_rebuttals: list[dict[str, str]]
    strength: str
    citations: list[dict[str, str]] = field(default_factory=list)

    def evidence_keys(self) -> list[str]:
        return [p["evidence"] for p in self.premises if p.get("evidence")]


VALID_KINDS = {"rebut", "undermine", "undercut"}
VALID_STRENGTHS = {"strong", "conditional"}


def _load_scheme(path: Path) -> Scheme:
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SchemeError(f"{path.name}: not a mapping")

    for required in ("id", "denial_reason", "side", "claim_template", "premises", "strength"):
        if not raw.get(required):
            raise SchemeError(f"{path.name}: missing {required}")

    if raw["strength"] not in VALID_STRENGTHS:
        raise SchemeError(f"{path.name}: strength must be one of {sorted(VALID_STRENGTHS)}")

    try:
        DenialReason(raw["denial_reason"])
    except ValueError:
        raise SchemeError(
            f"{path.name}: denial_reason {raw['denial_reason']!r} is not a DenialReason"
        ) from None

    for attack in raw.get("attacks") or []:
        if attack.get("kind") not in VALID_KINDS:
            raise SchemeError(f"{path.name}: attack kind must be one of {sorted(VALID_KINDS)}")

    for rebuttal in raw.get("known_rebuttals") or []:
        if not rebuttal.get("id") or not rebuttal.get("text"):
            raise SchemeError(f"{path.name}: every known rebuttal needs an id and text")
        if rebuttal.get("kind") not in VALID_KINDS:
            raise SchemeError(f"{path.name}: rebuttal kind must be one of {sorted(VALID_KINDS)}")

    for premise in raw["premises"]:
        if not premise.get("id") or not premise.get("text"):
            raise SchemeError(f"{path.name}: every premise needs an id and text")

    return Scheme(
        id=raw["id"],
        denial_reason=raw["denial_reason"],
        side=raw["side"],
        claim_template=" ".join(raw["claim_template"].split()),
        premises=raw["premises"],
        attacks=raw.get("attacks") or [],
        known_rebuttals=raw.get("known_rebuttals") or [],
        strength=raw["strength"],
        citations=raw.get("citations") or [],
    )


@lru_cache(maxsize=1)
def load_schemes() -> tuple[tuple[Scheme, ...], str]:
    """Every scheme, plus the library version."""
    version_path = SCHEMES_DIR / "VERSION"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else "0"

    schemes: list[Scheme] = []
    seen: set[str] = set()
    for path in sorted(SCHEMES_DIR.glob("*.yaml")):
        scheme = _load_scheme(path)
        if scheme.id in seen:
            raise SchemeError(f"duplicate scheme id {scheme.id!r}")
        seen.add(scheme.id)
        schemes.append(scheme)

    if not schemes:
        raise SchemeError("no schemes found; the argument graph would always be empty")
    return tuple(schemes), version


def schemes_for(reason: DenialReason) -> list[Scheme]:
    schemes, _ = load_schemes()
    return [s for s in schemes if s.denial_reason == reason.value]


@dataclass
class BuiltGraph:
    """The framework, before the solver runs."""

    arguments: list[Argument]
    attacks: list[Attack]
    schemes_version: str
    #: Evidence keys every instantiated argument depends on, deduped.
    evidence_keys: list[str]


def _render(template: str, facts: CaseFacts, service: str, condition: str) -> str:
    return template.format(
        service=service or "the requested service",
        insurer=facts.insurer_name or "the insurer",
        condition=condition or "this condition",
        state=facts.state,
    )


def build_framework(
    facts: CaseFacts,
    *,
    evidence_on_file: set[str] | None = None,
    service: str = "",
    condition: str = "",
) -> BuiltGraph:
    """Instantiate the schemes that match this case's stated denial reasons.

    ``evidence_on_file`` is the set of evidence keys the user has actually
    attached. It does not decide whether an argument exists — a scheme
    instantiates whether or not its evidence is present, and the UI shows the
    gap as "needs this to hold". What the evidence does change is whether a
    known rebuttal survives, and that in turn changes what the solver computes.
    """
    on_file = evidence_on_file or set()
    _, version = load_schemes()

    arguments: list[Argument] = []
    attacks: list[Attack] = []
    evidence_keys: list[str] = []

    # ---- the insurer's own arguments -------------------------------------
    for reason in facts.denial_reasons:
        insurer_id = f"{INSURER_PREFIX}{reason.value}"
        arguments.append(
            Argument(
                id=insurer_id,
                side="insurer",
                scheme_id=None,
                claim=INSURER_CLAIMS.get(reason, INSURER_CLAIMS[DenialReason.OTHER]),
                premises=[],
                required_evidence=[],
                citations=[Citation(source="denial_letter", locator="stated reason")],
                strength="conditional",
            )
        )

    # ---- counter-arguments, and the rebuttals to them --------------------
    for reason in facts.denial_reasons:
        insurer_id = f"{INSURER_PREFIX}{reason.value}"
        for scheme in schemes_for(reason):
            premises = [
                Premise(
                    id=p["id"],
                    text=p["text"],
                    evidence_key=p.get("evidence"),
                    satisfied=p.get("evidence") in on_file if p.get("evidence") else True,
                )
                for p in scheme.premises
            ]
            needed = scheme.evidence_keys()
            evidence_keys.extend(needed)

            arguments.append(
                Argument(
                    id=scheme.id,
                    side="patient",
                    scheme_id=scheme.id,
                    claim=_render(scheme.claim_template, facts, service, condition),
                    premises=premises,
                    required_evidence=needed,
                    citations=[
                        Citation(
                            source=c.get("source", "plan_document"),
                            locator=c.get("locator", ""),
                        )
                        for c in scheme.citations
                    ],
                    strength=scheme.strength,  # type: ignore[arg-type]
                )
            )

            for attack in scheme.attacks or [{"target": insurer_id, "kind": "rebut"}]:
                target = attack.get("target", insurer_id)
                # A scheme names its target as insurer.<reason>; keep it only if
                # that argument is actually in this case's framework.
                if target.startswith(INSURER_PREFIX) and target != insurer_id:
                    continue
                attacks.append(
                    Attack(
                        source_id=scheme.id,
                        target_id=target,
                        kind=attack.get("kind", "rebut"),  # type: ignore[arg-type]
                        note=f"Attacks the insurer's stated reason ({attack.get('kind')}).",
                    )
                )

            # Known rebuttals become real arguments, so defeat is computed.
            for rebuttal in scheme.known_rebuttals:
                rebuttal_id = rebuttal["id"]
                answer_key = rebuttal.get("defeated_by_evidence")
                if answer_key:
                    evidence_keys.append(answer_key)

                arguments.append(
                    Argument(
                        id=rebuttal_id,
                        side="insurer",
                        scheme_id=scheme.id,
                        claim=rebuttal["text"],
                        premises=[],
                        required_evidence=[],
                        citations=[],
                        strength="conditional",
                    )
                )
                attacks.append(
                    Attack(
                        source_id=rebuttal_id,
                        target_id=scheme.id,
                        kind=rebuttal["kind"],  # type: ignore[arg-type]
                        note="What the insurer is likely to say back.",
                    )
                )
                # The counter-argument attacks the rebuttal back, making the pair
                # a mutual attack while the point is unsettled.
                #
                # This is what produces the "Worth adding" tier, and it is a
                # modelling decision worth stating: a known rebuttal is what the
                # insurer *might* say, not a fact. A one-way attack would defeat
                # the counter-argument outright and the user would be told the
                # argument is dead when it is merely contestable. A mutual attack
                # yields two preferred extensions -- one where the argument holds,
                # one where the rebuttal does -- so the argument is credulously
                # but not sceptically acceptable. In the product's words: the
                # insurer has a fair answer to this one, so it is useful extra
                # weight rather than your main point.
                #
                # Attaching the evidence that answers the rebuttal breaks the
                # cycle below, and the argument becomes Solid ground.
                attacks.append(
                    Attack(
                        source_id=scheme.id,
                        target_id=rebuttal_id,
                        kind="rebut",
                        note=(
                            "The argument stands against this answer unless the insurer proves it."
                        ),
                    )
                )

                # The evidence that answers the rebuttal attacks it back. This is
                # the mechanism by which attaching a document moves an argument
                # from "Worth adding" to "Solid ground" -- and the solver, not
                # this module, is what notices.
                if answer_key and answer_key in on_file:
                    answer_id = f"{rebuttal_id}.answered"
                    arguments.append(
                        Argument(
                            id=answer_id,
                            side="patient",
                            scheme_id=scheme.id,
                            claim=(
                                f"That answer does not hold here: {answer_key.replace('_', ' ')} "
                                "is on file and settles the point."
                            ),
                            premises=[
                                Premise(
                                    id="evidence_on_file",
                                    text=f"{answer_key.replace('_', ' ')} is attached",
                                    evidence_key=answer_key,
                                    satisfied=True,
                                )
                            ],
                            required_evidence=[answer_key],
                            citations=[],
                            strength="strong",
                        )
                    )
                    attacks.append(
                        Attack(
                            source_id=answer_id,
                            target_id=rebuttal_id,
                            kind="undermine",
                            note="The evidence on file answers this.",
                        )
                    )

    return BuiltGraph(
        arguments=arguments,
        attacks=attacks,
        schemes_version=version,
        evidence_keys=sorted(set(evidence_keys)),
    )
