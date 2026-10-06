"""The argumentation engine. PURE: no network, no LLM, no database.

Builds a Dung abstract argumentation framework from schemes and confirmed facts,
then computes grounded, preferred and stable extensions with ASP encodings.
Acceptability is computed here, never asserted by the application and never by a
model.

Same import restriction as ``app.rules``, enforced by the same test.
"""

__all__: list[str] = []
