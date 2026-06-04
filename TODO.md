# PromptDB — Phase TODO Tracker

Living checklist; check off as completed. Source of truth for build progress.
Architecture & rationale: `PLAN.md`.

## P0 — Setup & scaffold ✅ DONE 2026-06-04
- [x] Read current LangGraph docs (install + StateGraph API); pinned langgraph 1.2.4 / langchain 1.3.4
- [x] Read current MCP Python SDK docs; pinned mcp 1.27.2 (FastMCP)
- [x] Confirm Python 3.12.3; venv created
- [x] `pyproject.toml` — deps + `promptdb` CLI entry point (hatchling, src layout)
- [x] `src/promptdb/` tree with stub modules (agent, cli, db, data, mcp_server, api, observability)
- [x] `.gitignore`, `.env.example`, README stub
- [x] Install deps into venv (editable + dev extras)
- [x] `git init` + first commit (local; no remote yet)
- [x] **Verify:** `promptdb --help` runs; imports resolve; smoke test passes

## P1 — Happy path (CLI Q&A on Chinook) ✅ DONE 2026-06-04
- [x] Load Chinook SQLite sample DB (11 tables)
- [x] `db/connection.py` — read-only SQLite connection + row cap (timeout in P2)
- [x] `db` — schema introspection (tables/columns/FKs)
- [x] `agent/state.py` — typed state
- [x] nodes: schema_retriever, sql_writer, sql_executor, answer_synthesizer (planner deferred)
- [x] `agent/graph.py` — wire linear happy-path graph
- [x] `cli/main.py` — `promptdb ask "question"` → run graph → print SQL + result table + answer
- [x] **Verify:** "which 5 artists earned the most revenue?" → Iron Maiden $138.60 (correct) ✓

## P2 — Self-correction + guardrails ✅ DONE 2026-06-04
- [x] `sql_validator` node — SELECT/WITH-only, single-statement, mutation-keyword block
- [x] conditional edges — validation OR execution error → back to sql_writer w/ error text; max 3 retries
- [x] graceful failure — exhausted retries → answer_synthesizer reports the last error
- [x] guardrails — SQLite statement timeout (progress handler) + row-limit cap + read-only connection
- [x] **Verify:** self-correction integration test recovers from a bad query (writer called 2×, rows returned) ✓
- [x] **Verify:** validator blocks DELETE/DROP/UPDATE/INSERT + stacked statements (unit tests) ✓

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
