"""MCP server exposing PromptDB's read-only database tools (FastMCP, stdio transport).

Any MCP client (Claude Desktop, the bundled client demo) can list tables, read the schema,
and run read-only SELECT queries. `run_sql` enforces the same guardrail as the agent, so
external callers are read-only too.
"""

from mcp.server.fastmcp import FastMCP
from sqlalchemy import inspect as sa_inspect

from promptdb.agent.guardrails import validate_sql
from promptdb.db.connection import get_engine, get_schema_text, run_select

mcp = FastMCP("promptdb")


@mcp.tool()
def list_tables() -> list[str]:
    """List the tables in the database."""
    return sa_inspect(get_engine()).get_table_names()


@mcp.tool()
def get_schema() -> str:
    """Return the database schema: tables, columns, and foreign keys."""
    return get_schema_text(get_engine())


@mcp.tool()
def run_sql(sql: str) -> dict:
    """Run a single read-only SELECT query. Returns {columns, rows} or {error}. Mutations are rejected."""
    err = validate_sql(sql)
    if err:
        return {"error": err}
    try:
        cols, rows = run_select(get_engine(), sql)
        return {"columns": cols, "rows": rows}
    except Exception as exc:  # noqa: BLE001 — return error to the MCP client
        return {"error": str(exc)}


def main() -> None:
    mcp.run()  # stdio transport


if __name__ == "__main__":
    main()
