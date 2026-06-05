"""Sample database config — points at an existing read-only database (the FireScope wildfire DB).

Used server-side only: the connection string never leaves the server, the agent is shown only an
allowlist of non-PII tables, and a guardrail blocks any query that references a denied table.
"""

import os


def sample_url() -> str | None:
    """Server-side connection string for the sample DB, or None if unconfigured."""
    return os.environ.get("PROMPTDB_SAMPLE_ADMIN_URL") or None


def sample_tables() -> list[str] | None:
    """Allowlist of tables shown to the agent for the sample DB (None = all)."""
    raw = os.environ.get("PROMPTDB_SAMPLE_TABLES", "").strip()
    names = [t.strip() for t in raw.split(",") if t.strip()]
    return names or None


def denied_tables() -> set[str]:
    """Tables a sample query must never touch (PII), enforced by the guardrail."""
    raw = os.environ.get("PROMPTDB_SAMPLE_DENY", "").strip()
    return {t.strip().lower() for t in raw.split(",") if t.strip()}
