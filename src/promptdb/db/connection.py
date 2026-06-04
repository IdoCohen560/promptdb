"""Read-only DB access + schema introspection. (Full RO hardening lands in P2.)"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, inspect, text

load_dotenv()

DEFAULT_URL = "sqlite:///chinook.db"
MAX_ROWS = 100


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


def run_select(engine: Engine, sql: str, max_rows: int = MAX_ROWS) -> tuple[list[str], list[list]]:
    """Execute a query read-only and return (columns, rows). Raises on SQL error."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [list(r) for r in result.fetchmany(max_rows)]
    return cols, rows
