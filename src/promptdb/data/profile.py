"""Read-only data profiling: per-table row counts and per-column null rate + distinct count."""

from sqlalchemy import Engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text

from promptdb.db.connection import get_engine


def profile_db(engine: Engine | None = None) -> list[dict]:
    """Profile every table: row count, and for each column its null % and distinct count."""
    engine = engine or get_engine()
    insp = sa_inspect(engine)
    out: list[dict] = []
    with engine.connect() as conn:
        for table in insp.get_table_names():
            n = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0
            cols = []
            for c in insp.get_columns(table):
                name = c["name"]
                nulls = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{table}" WHERE "{name}" IS NULL')
                ).scalar() or 0
                distinct = conn.execute(
                    text(f'SELECT COUNT(DISTINCT "{name}") FROM "{table}"')
                ).scalar() or 0
                cols.append({
                    "col": name,
                    "null_pct": (100.0 * nulls / n) if n else 0.0,
                    "distinct": distinct,
                })
            out.append({"table": table, "rows": n, "columns": cols})
    return out
