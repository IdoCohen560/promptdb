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
