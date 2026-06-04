"""Read-only data-quality checks: orphaned foreign keys, empty tables, high-null columns."""

from sqlalchemy import Engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text

from promptdb.data.profile import profile_db
from promptdb.db.connection import get_engine

NULL_THRESHOLD = 50.0


def check_quality(engine: Engine | None = None) -> list[dict]:
    """Return a list of data-quality issues, each {severity, table, issue}."""
    engine = engine or get_engine()
    insp = sa_inspect(engine)
    issues: list[dict] = []

    with engine.connect() as conn:
        for table in insp.get_table_names():
            for fk in insp.get_foreign_keys(table):
                ccols = fk.get("constrained_columns") or []
                pcols = fk.get("referred_columns") or []
                parent = fk.get("referred_table")
                if parent and len(ccols) == 1 and len(pcols) == 1:
                    c, p = ccols[0], pcols[0]
                    orphans = conn.execute(text(
                        f'SELECT COUNT(*) FROM "{table}" ch WHERE ch."{c}" IS NOT NULL '
                        f'AND ch."{c}" NOT IN (SELECT pa."{p}" FROM "{parent}" pa)'
                    )).scalar() or 0
                    if orphans:
                        issues.append({"severity": "high", "table": table,
                                       "issue": f"{orphans} orphaned rows: {table}.{c} -> {parent}.{p}"})

    for t in profile_db(engine):
        if t["rows"] == 0:
            issues.append({"severity": "medium", "table": t["table"], "issue": "table is empty"})
            continue
        for col in t["columns"]:
            if col["null_pct"] > NULL_THRESHOLD:
                issues.append({"severity": "low", "table": t["table"],
                               "issue": f"{col['col']} is {col['null_pct']:.0f}% null"})
    return issues
