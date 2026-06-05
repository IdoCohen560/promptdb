# Use your own database

The hosted demo queries a bundled sample database. To query **your** data, run the local connector
so the agent operates where your data lives. Your database credentials and rows never leave your
machine; only the schema and your own query results are sent to the model.

This is the [Model Context Protocol](https://modelcontextprotocol.io) pattern: a small server runs
locally and exposes read-only database tools to any MCP client (Claude Desktop, Cursor) or to the
PromptDB CLI directly.

## Install

```bash
pipx install git+https://github.com/IdoCohen560/promptdb
# or, from a clone:
pip install -e ".[providers]"
```

## Point it at your database

Set `PROMPTDB_DATABASE_URL` to any SQLAlchemy URL.

```bash
# SQLite
export PROMPTDB_DATABASE_URL="sqlite:///./mystore.db"

# PostgreSQL / MySQL — use a READ-ONLY database user (see "Other engines" below)
export PROMPTDB_DATABASE_URL="postgresql://readonly_user:pw@localhost:5432/mydb"
```

Then query from the CLI:

```bash
promptdb ask "top 5 products by total revenue last quarter"
promptdb schema      # ER diagram of your database
promptdb doctor      # orphaned foreign keys, empty tables, high-null columns
```

## Plug into Claude Desktop

Add the connector to your Claude Desktop config
(`claude_desktop_config.json` — see [`examples/claude_desktop_config.json`](../examples/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "promptdb": {
      "command": "promptdb-mcp",
      "env": { "PROMPTDB_DATABASE_URL": "sqlite:////absolute/path/to/mystore.db" }
    }
  }
}
```

Restart Claude Desktop. It can now call `list_tables`, `get_schema`, and a guardrailed `run_sql`
against your database, all read-only.

## Bring your own model

The connector and CLI honor the same provider router as the hosted app:

```bash
PROMPTDB_PROVIDER=anthropic PROMPTDB_MODEL=claude-sonnet-4-6 promptdb ask "..."
PROMPTDB_PROVIDER=openai    PROMPTDB_MODEL=gpt-4o-mini       promptdb ask "..."
PROMPTDB_PROVIDER=ollama    PROMPTDB_MODEL=gemma2            promptdb ask "..."   # fully local, $0
```

Running Ollama locally plus the local connector means **nothing leaves your machine at all** — the
database, the model, and the agent all run on your hardware.

## Other engines (Postgres, MySQL, …)

The mutation validator works across dialects, but two read-only protections are SQLite-specific:
the `mode=ro` connection and the statement-timeout progress handler. For other engines, get the
same guarantees from the database itself:

- Connect as a **read-only user** (e.g. `GRANT SELECT` only).
- Set a server-side `statement_timeout` (Postgres) or equivalent.

With a read-only user the agent is physically unable to write, regardless of the application layer.
