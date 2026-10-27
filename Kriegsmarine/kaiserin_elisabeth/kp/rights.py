"""Rights filter for anything shown in the public demo or the public repo.

edmRightsReusePolicy is a LIST in v2 (one record returned ["OPEN", "RESTRICTED"]),
with one entry per rights statement. A scalar comparison like == "OPEN" silently
fails; `"OPEN" in value` alone lets restricted items through. An item counts as
open only if every statement it carries is OPEN.

Values seen 2026-10-27: OPEN, RESTRICTED, CLOSED (874 records mix OPEN and CLOSED).
"""

from __future__ import annotations

# Server-side equivalent of is_open for /v2/search and /v2/similar `filter_by`
# (584,589 records on 2026-10-27). Keep in step with is_open.
OPEN_FILTER = (
    "edmRightsReusePolicy:=OPEN && edmRightsReusePolicy:!=RESTRICTED"
    " && edmRightsReusePolicy:!=CLOSED"
)


def policies(document: dict) -> list[str]:
    value = document.get("edmRightsReusePolicy") or []
    return [value] if isinstance(value, str) else list(value)


def is_open(document: dict) -> bool:
    """True only if the record has at least one policy and all of them are OPEN."""
    p = policies(document)
    return bool(p) and all(x == "OPEN" for x in p)


def open_only(documents: list[dict]) -> list[dict]:
    return [d for d in documents if is_open(d)]


def label(document: dict) -> str:
    """Short licence label for captions, e.g. "CC0 / CC BY-NC"."""
    names = document.get("edmRightsName") or []
    return " / ".join(names) if names else "rights unknown"
