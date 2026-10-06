"""Entry point.

    uvicorn main:app --reload

Render's start command is ``uvicorn main:app --host 0.0.0.0 --port $PORT``, so
this module sits at the backend root where that command expects it. The app
itself is assembled in :mod:`app.main`; keeping the package structure is what
makes the neurosymbolic boundary enforceable, because the boundary is defined in
terms of which packages may import which.
"""

from __future__ import annotations

from app.main import app

__all__ = ["app"]
