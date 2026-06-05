"""Read-only SQL guardrails: only a single SELECT/WITH query is allowed through.

This is defense-in-depth on top of the read-only DB connection — it rejects mutations
*before* execution and gives the agent a clear error to self-correct from.
"""

import re
from typing import Optional

# Statement-initiating mutation keywords. A read-only SELECT never contains these as
# bare tokens. \b treats "_" as a word char, so "last_update" does NOT match "update".
_MUTATION_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|attach|detach)\b", re.IGNORECASE
)

# Table referenced after FROM or JOIN (optionally schema-qualified / quoted).
_TABLE_RE = re.compile(r'\b(?:from|join)\s+["\']?(?:\w+\.)?(\w+)', re.IGNORECASE)

# A column wildcard in the select list ("SELECT *", "SELECT t.*", ", *") — NOT count(*).
_STAR_RE = re.compile(r"select\s+(?:distinct\s+)?\*|,\s*\*|\b\w+\.\*", re.IGNORECASE)


def validate_sql(sql: str) -> Optional[str]:
    """Return an error string if `sql` is not a safe single read-only query, else None."""
    if not sql or not sql.strip():
        return "empty query"
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        return "multiple statements are not allowed; submit a single SELECT"
    tokens = s.split()
    first = tokens[0].lower() if tokens else ""
    if first not in ("select", "with"):
        return f"only read-only SELECT/WITH queries are allowed (started with '{first}')"
    m = _MUTATION_RE.search(s)
    if m:
        return f"forbidden mutation keyword: '{m.group(1).lower()}'"
    return None


def validate_table_access(sql: str, denied: set[str]) -> Optional[str]:
    """Reject a query that reads from a denied table (e.g. PII tables on the sample DB)."""
    if not denied:
        return None
    refs = {t.lower() for t in _TABLE_RE.findall(sql)}
    blocked = refs & denied
    if blocked:
        return f"this sample database does not expose: {', '.join(sorted(blocked))}"
    return None


def validate_credentials(sql: str, deny_columns: set[str], star_tables: set[str]) -> Optional[str]:
    """Keep credential material out of the public demo: block any reference to a denied column
    (e.g. password_hash), and block `SELECT *` on tables that hold one (so it can't leak via a
    wildcard). The full schema is still visible and everything else is queryable."""
    if not deny_columns and not star_tables:
        return None
    low = sql.lower()
    for c in deny_columns:
        if re.search(rf"\b{re.escape(c.lower())}\b", low):
            return f"the demo does not expose the '{c}' column"
    if _STAR_RE.search(sql):
        for t in star_tables:
            if re.search(rf"\b{re.escape(t.lower())}\b", low):
                return f"select explicit columns instead of * from '{t}' in the demo"
    return None
