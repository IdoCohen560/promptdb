# PromptDB

> Ask your database in English. A production text-to-SQL agent built on LangGraph.

Point PromptDB at a SQL database and ask questions in plain English. It reads the schema,
writes SQL, runs it **read-only**, **self-corrects** on errors, and explains the answer —
with eval-measured accuracy, LangSmith tracing, and per-query cost tracking.

```
$ promptdb ask "which 5 artists earned the most revenue?"
SQL: SELECT ar.Name, ROUND(SUM(il.UnitPrice*il.Quantity),2) AS rev FROM Artist ar
     JOIN Album al ... GROUP BY ar.ArtistId ORDER BY rev DESC LIMIT 5
┏━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name         ┃ rev      ┃   Iron Maiden leads with $138.60, ahead of U2 ($105.93)…
┗━━━━━━━━━━━━━━┻━━━━━━━━━━┛
· 2.1s · $0.00539 · 1 attempt(s)
```

## Results
| Benchmark | Metric | Result |
|---|---|---|
| **Spider dev sample (150 Q)** | strict execution accuracy | **69.3%** (104/150), $0.0038/query |
| Chinook gold set (12 Q) | execution accuracy (subset-tolerant) | 100% (12/12) |

Model trade-off on the gold set:

| Model | Accuracy | Cost/query | Latency |
|---|---|---|---|
| claude-sonnet-4-6 | 100.0% | $0.00539 | 2.6s |
| claude-haiku-4-5 | 91.7% | $0.00177 | 1.1s |

## Architecture
A LangGraph state machine with a self-correction loop — a validation or execution error
routes back to the writer (with the error in context) until it succeeds or hits the retry cap.

```mermaid
flowchart LR
    Q[question] --> SR[schema_retriever]
    SR --> SW[sql_writer]
    SW --> V[sql_validator]
    V -->|valid| EX[sql_executor]
    V -->|invalid, retries left| SW
    EX -->|ok| AS[answer_synthesizer]
    EX -->|error, retries left| SW
    AS --> OUT[answer + SQL + cost]
```

**Guardrails (read-only by design):** the validator allows only single `SELECT`/`WITH`
statements and blocks `INSERT/UPDATE/DELETE/DROP/...`; the DB connection is opened read-only;
queries have a statement timeout and a row cap. The agent can never modify data.

## Quickstart
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,web]"
cp .env.example .env          # add ANTHROPIC_API_KEY
curl -sSL -o chinook.db "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
promptdb ask "how many customers are there?"
```

## Usage
**CLI (flagship)**
```bash
promptdb ask "which countries have more than 5 customers?"
promptdb schema            # Mermaid ER diagram from introspection
promptdb profile           # row counts, null %, distinct counts (read-only)
promptdb doctor            # data-quality issues: orphaned FKs, empty tables, high-null columns
```

**MCP server** — exposes `list_tables`, `get_schema`, `run_sql` (guardrailed) to any MCP client:
```bash
python scripts/mcp_client_demo.py        # stdio round-trip demo
# Claude Desktop: { "mcpServers": { "promptdb": { "command": ".../.venv/bin/promptdb-mcp" } } }
```

**Web demo** — FastAPI streaming UI (watch the agent's steps live):
```bash
uvicorn promptdb.api.main:app --reload   # http://localhost:8000
docker build -t promptdb . && docker run -p 8000:8000 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY promptdb
```

## Evals
```bash
python -m evals.run_evals          # Chinook gold set: accuracy, per-difficulty, cost
python -m evals.compare_models     # Sonnet vs Haiku accuracy/cost
python -m evals.run_spider 150     # Spider dev sample (questions: xlangai/spider, DBs: premai-io/spider)
```
Metric: execution accuracy (compare result sets, order-insensitive). Spider uses strict match
for comparability; the Chinook set uses column-subset tolerance to forgive extra columns.
CI runs `pytest` on every push; the paid eval suite runs on manual dispatch.

## Stack
Python · LangGraph + LangChain · Claude (Anthropic) · SQLAlchemy · MCP · Typer + Rich ·
FastAPI · LangSmith · pytest · Docker · GitHub Actions.

## Observability & cost
Every query tracks token cost (CLI footer `· 2.1s · $0.005 · 1 attempt(s)`). LangSmith tracing
turns on automatically when `LANGSMITH_API_KEY` and `LANGSMITH_TRACING=true` are set.
