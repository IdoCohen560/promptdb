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

## P2.5 — MCP layer ✅ DONE 2026-06-04 (Claude Desktop step pending Ido)
- [x] `mcp_server` (FastMCP) — run_sql (guardrailed), get_schema, list_tables; `promptdb-mcp` entry point
- [x] consumption proven via `scripts/mcp_client_demo.py` (real stdio round-trip) — design note: core
      agent stays direct for fast evals; MCP server + client demo prove both sides without a subprocess hop
- [x] **Verify:** server runs; client lists tools, run_sql(SELECT) returns rows, run_sql(DELETE) rejected ✓
- [ ] **Verify (manual, needs Ido):** plug `promptdb-mcp` into Claude Desktop and query live (config in README)

## P3 — Eval harness ✅ HARNESS DONE 2026-06-04 (Spider = headline stretch)
- [x] `evals/dataset.py` — Chinook gold set (12 Qs, 6 difficulty buckets); Spider plugs in behind same interface
- [x] `evals/evaluators.py` — column-subset-tolerant execution match (handles extra/reordered cols)
- [x] `evals/run_evals.py` — accuracy, per-difficulty breakdown, latency, token cost; writes results/latest.json
- [x] failure-mode bucketing (simple/filter/aggregation/join/group_having/nested)
- [x] shared prompt (`build_sql_prompt`) so evals measure the REAL agent
- [x] CI — pytest on push (`test.yml`); paid evals on manual dispatch (`evals.yml`), not per-push
- [x] **Verify:** harness runs, 12/12 on Chinook sanity set, $0.0054/query, 2.2s avg ✓
- [x] **HEADLINE (P3b):** Spider dev sample — 104/150 = 69.3% strict execution accuracy, $0.0038/query
      (claude-sonnet-4-6); `evals/run_spider.py` — questions: xlangai/spider, DBs: premai-io/spider

## P4 — Observability + cost ✅ DONE 2026-06-04 (LangSmith live-view pending Ido)
- [x] LangSmith tracing — auto via env vars; `observability/tracing.py` status helper
- [x] `observability/cost.py` — per-query token + cost; cumulative `cost_usd` in state; CLI footer
- [x] 2-model comparison (`evals/compare_models.py`): Sonnet 100% $0.0054/q 2.6s | Haiku 91.7% $0.0018/q 1.1s
- [x] **Verify:** cost footer live; comparison discriminates models ✓
- [ ] **Verify (manual, needs Ido):** LangSmith traces visible (set LANGSMITH_API_KEY + LANGSMITH_TRACING=true)

## P4.5 — Data copilot (Tier 2, read-only) ✅ DONE 2026-06-04
- [x] `data/schema_graph.py` — FK introspection → Mermaid ER diagram; `promptdb schema [--output f]`
- [x] `data/profile.py` — row counts, null %, distinct counts; `promptdb profile`
- [x] `data/quality.py` — orphaned FKs, empty tables, high-null columns; `promptdb doctor`
- [x] **Verify:** all three work on Chinook (read-only) + 3 tests ✓

## P5 — Deploy + UI ✅ BUILT 2026-06-04 (deploy needs Ido's host)
- [x] `api/main.py` — FastAPI /query + /query/stream (SSE) + /health; API-key auth, per-IP rate limit, request-id logging
- [x] `web/index.html` — streaming steps UI, SQL box, result table, answer, cost footer (FastAPI-served, single deployable)
- [x] `Dockerfile` — self-contained (bakes Chinook), uvicorn
- [x] **Verify (local):** /health, POST /query, SSE live node stream, index served ✓
- [ ] **Verify (needs host):** deploy to Render/Railway → live URL + Playwright screenshots

## P6 — README + resume ✅ DONE 2026-06-04 (demo video pending Ido)
- [x] README — architecture (Mermaid), results table (Spider 69.3% + model comparison), usage, setup, stack
- [x] resume bullet filled with real numbers (PLAN.md)
- [ ] record 60s demo video / asciinema GIF (script in PLAN.md) — pending Ido
- [x] **Verify:** README complete; bullet drafted ✓

## P7 — Computer-use (OPTIONAL stretch)
- [ ] `browser/computer_use.py` — Playwright in Docker drives a web SQL console
- [ ] vision model reads result screenshot
- [ ] toggle between tool-calling and vision-action paths
- [ ] **Verify:** agent answers via browser-driven console; both paths comparable
