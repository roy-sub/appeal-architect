# Appeal Architect backend.
#
# Multi-stage so the build toolchain does not ship. Python 3.12 for parity with
# the spec's stack; the code is 3.12-compatible and also runs on 3.13.
#
# The runtime needs system libraries for two jobs:
#   * OCR of scanned denial letters (tesseract) -- English language pack ONLY.
#     The full language set is hundreds of megabytes and we need one language.
#   * PDF rendering of the generated appeal letter (WeasyPrint's cairo/pango stack).

# ──────────────────────────────── builder ────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# clingo and pillow may build from source on some platforms; give them a compiler.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      cmake \
      libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app

# Install into a prefix we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install .

# ──────────────────────────────── runtime ────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
      # OCR -- English only, deliberately
      tesseract-ocr \
      tesseract-ocr-eng \
      # WeasyPrint's rendering stack (spec 15)
      libcairo2 \
      libpango-1.0-0 \
      libpangocairo-1.0-0 \
      libgdk-pixbuf-2.0-0 \
      libffi8 \
      shared-mime-info \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app ./app
COPY pyproject.toml ./

# Run unprivileged. Nothing here writes to the filesystem at runtime -- uploads
# go to Supabase Storage, not to disk.
RUN useradd --create-home --uid 10001 appeal \
    && chown -R appeal:appeal /app
USER appeal

EXPOSE 8000

# Render's free web service sleeps after 15 minutes idle and sets $PORT.
# The frontend shows a warming state on the first call rather than an error
# (spec 15), and an external uptime monitor pings /healthz.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,os,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/healthz', timeout=4).status==200 else 1)"

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
