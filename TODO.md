# PromptDB — Phase TODO Tracker

Living checklist; check off as completed. Source of truth for build progress.
Architecture & rationale: `PLAN.md`.

## P0 — Setup & scaffold
- [ ] Read current LangGraph docs (install + StateGraph API); pin version
- [ ] Read current MCP Python SDK docs; pin version
- [ ] Confirm Python 3.11+; create venv
- [ ] `pyproject.toml` — deps + `promptdb` CLI entry point
- [ ] `src/` tree with stub modules (agent, cli, db, data, mcp_server, api, observability)
- [ ] `.gitignore`, `.env.example`, README stub
- [ ] Install deps into venv
- [ ] `git init` + first commit
- [ ] **Verify:** `promptdb --help` runs without error

## P1 — Happy path (CLI Q&A on Chinook)
- [ ] Load Chinook SQLite sample DB
- [ ] `db/connection.py` — read-only connection + row cap + timeout
- [ ] `db` — schema introspection (tables/columns/FKs)
- [ ] `agent/state.py` — typed state
- [ ] nodes: schema_retriever, planner, sql_writer, sql_executor, answer_synthesizer
- [ ] `agent/graph.py` — wire linear happy-path graph
- [ ] `cli/main.py` — `promptdb "question"` → run graph → print SQL + result + answer
- [ ] **Verify:** "which 5 artists earned the most revenue?" correct end-to-end

## P2 — Self-correction + guardrails
- [ ] `sql_validator` node — SELECT-only allow-list, block DDL/DML, column-existence check
- [ ] conditional edge — on execution error → back to sql_writer w/ error text; max N retries
- [ ] graceful-failure node when retries exhausted
- [ ] guardrails — query timeout, row-limit cap, read-only DB user
- [ ] **Verify:** error-inducing question recovers within N retries
- [ ] **Verify:** a DELETE/DROP attempt is blocked by the validator

## P2.5 — MCP layer
- [ ] `mcp_server` — expose run_sql, get_schema, list_tables as MCP tools
- [ ] agent consumes tools via MCP client (not direct calls)
- [ ] **Verify:** server runs; agent answers via MCP
- [ ] **Verify:** server plugs into Claude Desktop and answers a query live

## P3 — Eval harness
- [ ] `evals/dataset.py` — load Spider dev subset (~100–200 Qs) + DBs
- [ ] `evals/evaluators.py` — execution-accuracy, exact-set-match, latency, cost
- [ ] `evals/run_evals.py` — run agent over set, write results
- [ ] failure-mode bucketing (joins / aggregations / nested / ambiguity)
- [ ] `.github/workflows/evals.yml` — run evals on push
- [ ] **Verify:** real execution-accuracy % + failure-mode table

## P4 — Observability + cost
- [ ] LangSmith tracing on all nodes
- [ ] `observability/cost.py` — per-query token + cost tracking
- [ ] 2-model comparison (Claude vs cheaper) accuracy + cost
- [ ] **Verify:** traces visible in LangSmith; cost logged; comparison table

## P4.5 — Data copilot (Tier 2, read-only)
- [ ] `data/schema_graph.py` — FK introspection → Mermaid/Graphviz ER diagram; `promptdb schema`
- [ ] `data/profile.py` — row counts, null rates, cardinality, distributions; `promptdb profile`
- [ ] `data/quality.py` — orphaned FKs, dupes, unexpected nulls, type anomalies; `promptdb doctor`
- [ ] **Verify:** all three commands work on Chinook (read-only)

## P5 — Deploy + UI
- [ ] `api/main.py` — FastAPI /query + rate limit + API-key auth + structured logging
- [ ] `app/streamlit_app.py` — streaming steps, SQL box, result table, schema diagram, profile
- [ ] Dockerfile + container build
- [ ] deploy to Render/Railway/Fly → live URL
- [ ] **Verify:** live URL works; Playwright screenshots mobile/desktop

## P6 — README + resume
- [ ] README — architecture diagram, eval table, CLI asciinema GIF, live link, setup
- [ ] record 60s demo video (script in PLAN.md)
- [ ] fill resume bullet X/Y from P3/P4 numbers
- [ ] **Verify:** README complete; bullet drafted

## P7 — Computer-use (OPTIONAL stretch)
- [ ] `browser/computer_use.py` — Playwright in Docker drives a web SQL console
- [ ] vision model reads result screenshot
- [ ] toggle between tool-calling and vision-action paths
- [ ] **Verify:** agent answers via browser-driven console; both paths comparable
