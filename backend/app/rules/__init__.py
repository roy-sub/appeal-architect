"""The rules engine. PURE: no network, no LLM, no database.

Determines the appeal route, the review levels, the deadlines and the required
elements, from confirmed facts only.

This package may import: the standard library, ``clingo``, ``clorm``,
``pydantic``, ``dateutil``, ``holidays``, and ``app.domain``. It may not import
``anthropic``, ``httpx``, ``requests``, ``app.services.llm`` or ``app.db`` --
directly or transitively. ``tests/test_boundary.py`` walks the import closure and
fails the build if one appears.

That restriction is the product, not a style preference: it is what makes "the
LLM never computes a deadline" a fact about the code rather than a promise in a
README.
"""

__all__: list[str] = []
