"""Deterministically remove direct identifiers from released source excerpts.

This transformation is for the anonymous review archive. The archive records
original and released hashes for every changed member so the numerical results
remain auditable without distributing email addresses or user-home directory
names from repository excerpts.
"""

from __future__ import annotations

import re


TEXT_SUFFIXES = {".bib", ".cls", ".csv", ".json", ".jsonl", ".md", ".py", ".svg", ".tex", ".toml"}
EMAIL = re.compile(rb"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![A-Z0-9.-])")
HOME = re.compile(rb"/(Users|home)/(?!REDACTED_USER/)[A-Za-z0-9_.-]+/")


def redact_bytes(data: bytes) -> tuple[bytes, dict[str, int]]:
    """Redact identifiers while preserving valid UTF-8, CSV, and JSON syntax."""
    data.decode("utf-8")
    data, email_count = EMAIL.subn(b"[EMAIL_REDACTED]", data)
    data, home_count = HOME.subn(lambda match: b"/" + match.group(1) + b"/REDACTED_USER/", data)
    return data, {"email_like": email_count, "home_path": home_count}


def remaining_direct_identifiers(data: bytes) -> dict[str, int]:
    return {"email_like": len(EMAIL.findall(data)), "home_path": len(HOME.findall(data))}
