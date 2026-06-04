"""Schema -> Mermaid ER diagram, built from read-only introspection (no RAG, no graphify)."""

from sqlalchemy import Engine
from sqlalchemy import inspect as sa_inspect

from promptdb.db.connection import get_engine


def mermaid_er(engine: Engine | None = None) -> str:
    """Return a Mermaid `erDiagram` of tables, columns (with PKs), and foreign-key relations."""
    engine = engine or get_engine()
    insp = sa_inspect(engine)
    lines = ["erDiagram"]
    for table in insp.get_table_names():
        pk = set(insp.get_pk_constraint(table).get("constrained_columns") or [])
        lines.append(f"    {table} {{")
        for c in insp.get_columns(table):
            ctype = str(c["type"]).split("(")[0].replace(" ", "_") or "col"
            tag = " PK" if c["name"] in pk else ""
            lines.append(f"        {ctype} {c['name']}{tag}")
        lines.append("    }")
    for table in insp.get_table_names():
        for fk in insp.get_foreign_keys(table):
            parent = fk.get("referred_table")
            if parent:
                lines.append(f"    {parent} ||--o{{ {table} : has")
    return "\n".join(lines)
