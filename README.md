# PromptDB

> Ask your database in English. A production text-to-SQL agent built on LangGraph.

**Status:** in development — see `TODO.md` for phase progress and `PLAN.md` for architecture.

## What it does
Point PromptDB at a SQL database and ask questions in plain English. It reads the schema,
writes SQL, runs it **read-only**, self-corrects on errors, and explains the result —
with eval-measured accuracy, LangSmith tracing, and per-query cost tracking.

## Quickstart (dev)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in ANTHROPIC_API_KEY
promptdb --help
```

## Interfaces
- **CLI (flagship):** `promptdb ask "which 5 artists earned the most revenue?"`
- **MCP server:** exposes the DB tools to any MCP client (see below)
- **Web/API:** FastAPI + streaming UI (P5)

### MCP server
The same read-only DB tools (`list_tables`, `get_schema`, `run_sql`) are exposed over MCP
so any client can use them. `run_sql` enforces the SELECT-only guardrail.

Round-trip demo (spawns the server over stdio and calls its tools):
```bash
python scripts/mcp_client_demo.py
```

Plug into Claude Desktop — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "promptdb": { "command": "/home/cohedo/promptdb/.venv/bin/promptdb-mcp" }
  }
}
```

_(README expands at P6 with architecture diagram, eval results, and demo.)_
