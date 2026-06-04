"""Read-only DB access + schema introspection. (Full RO hardening lands in P2.)"""

import os
import time
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, inspect, text

load_dotenv()

DEFAULT_URL = "sqlite:///chinook.db"
MAX_ROWS = 100
TIMEOUT_S = 5.0


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Engine for the configured database. SQLite is opened read-only."""
    url = os.environ.get("PROMPTDB_DATABASE_URL", DEFAULT_URL)
    if url.startswith("sqlite:///") and "mode=ro" not in url:
        path = url.removeprefix("sqlite:///")
        url = f"sqlite:///file:{path}?mode=ro&uri=true"
    return create_engine(url)


def get_schema_text(engine: Engine) -> str:
    """Compact schema description (tables, columns, foreign keys) for the LLM prompt."""
    insp = inspect(engine)
    lines: list[str] = []
    for table in insp.get_table_names():
        cols = ", ".join(f"{c['name']} {c['type']}" for c in insp.get_columns(table))
        lines.append(f"TABLE {table}({cols})")
        for fk in insp.get_foreign_keys(table):
            if fk.get("referred_table"):
                src = ",".join(fk["constrained_columns"])
                dst = ",".join(fk["referred_columns"])
                lines.append(f"  FK {table}.{src} -> {fk['referred_table']}.{dst}")
    return "\n".join(lines)


def run_select(
    engine: Engine, sql: str, max_rows: int = MAX_ROWS, timeout_s: float = TIMEOUT_S
) -> tuple[list[str], list[list]]:
    """Execute a query read-only, aborting after timeout_s. Returns (columns, rows); raises on error."""
    with engine.connect() as conn:
        raw = getattr(conn.connection, "dbapi_connection", None)
        # SQLite statement timeout via progress handler (Postgres would use statement_timeout).
        if raw is not None and hasattr(raw, "set_progress_handler"):
            start = time.monotonic()
            raw.set_progress_handler(
                lambda: 1 if time.monotonic() - start > timeout_s else 0, 10_000
            )
        try:
            result = conn.execute(text(sql))
            cols = list(result.keys())
            rows = [list(r) for r in result.fetchmany(max_rows)]
        finally:
            if raw is not None and hasattr(raw, "set_progress_handler"):
                raw.set_progress_handler(None, 0)
    return cols, rows
