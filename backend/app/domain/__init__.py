"""Shared vocabulary.

Imported by the pure engine packages (``app.rules``, ``app.argumentation``), so
this package must stay free of network, database and LLM dependencies. The
boundary test walks the transitive import closure and fails the build otherwise.
"""
