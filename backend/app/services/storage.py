"""Private buckets and short-lived signed URLs.

Objects are laid out as ``{case_id}/{uuid}-{filename}``, so the first path
segment is the case and ownership follows from it — which is what the storage
RLS policy in migration 001 keys on.

No file is ever served from a public URL. The browser reaches a document only
through a signed URL that expires.
"""

from __future__ import annotations

import re
import uuid
from typing import Literal

from app.db.client import get_client

Bucket = Literal["documents", "letters"]

#: Signed URLs live long enough to open a document and not much longer.
SIGNED_URL_TTL_SECONDS = 600

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    """A filename safe for a storage key, with the extension kept.

    User-supplied filenames reach a path, so they are sanitised rather than
    trusted: a name containing ``../`` would otherwise address another case's
    prefix.
    """
    cleaned = _UNSAFE.sub("_", name.strip()) or "upload"
    return cleaned[-120:]


def object_path(case_id: str, filename: str) -> str:
    return f"{case_id}/{uuid.uuid4().hex}-{safe_filename(filename)}"


def upload(bucket: Bucket, path: str, data: bytes, content_type: str) -> str:
    get_client().storage.from_(bucket).upload(
        path, data, {"content-type": content_type, "upsert": "false"}
    )
    return path


def signed_url(bucket: Bucket, path: str, *, ttl: int = SIGNED_URL_TTL_SECONDS) -> str:
    result = get_client().storage.from_(bucket).create_signed_url(path, ttl)
    url = result.get("signedURL") or result.get("signedUrl") or ""
    if not url:  # pragma: no cover
        raise RuntimeError("Supabase did not return a signed URL")
    return str(url)


def remove(bucket: Bucket, paths: list[str]) -> None:
    if paths:
        get_client().storage.from_(bucket).remove(paths)


def remove_case_objects(bucket: Bucket, case_id: str) -> int:
    """Delete every object under a case's prefix. Used by the hard delete."""
    client = get_client()
    try:
        listing = client.storage.from_(bucket).list(case_id)
    except Exception:
        return 0
    paths = [f"{case_id}/{item['name']}" for item in listing or [] if item.get("name")]
    if paths:
        client.storage.from_(bucket).remove(paths)
    return len(paths)
