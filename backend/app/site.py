"""Fixed strings. Verbatim, everywhere they appear.

These are product constants, not copy to be improved in passing. The disclaimer
is a legal positioning statement as much as a brand one, and it appears in the
footer and in **every** generated letter.
"""

DISCLAIMER = (
    "Appeal Architect prepares documents and explains procedure. It is not legal or "
    "medical advice, and it does not represent you. You review and file everything "
    "yourself."
)

PRODUCT_NAME = "Appeal Architect"
PRIMARY_PROMISE = "Your denial, formally refuted."
METHOD_PROMISE = "Every paragraph backed by a rule."


def rules_stamp(as_of: str, version: str) -> str:
    """The stamp shown on every route determination."""
    return f"Rules current as of {as_of} · version {version}"
