# Changelog

All notable changes to PromptDB are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Live hosted demo** — Next.js "blueprint" UI on Vercel backed by the agent API on Render.
  Streams the agent's pipeline, renders the schema as an ER diagram, shows generated SQL, results
  with inline data bars, and per-query cost.
- **Multi-provider model router** — bring your own key for Anthropic, OpenAI, or a local Ollama
  model. The per-request model is injected via LangGraph config, so keys never enter graph state
  or traces. Default (demo) path stays on the server key.
- **Demo spend protection** — per-IP free-query cap plus a global daily spend ceiling on the
  server key; bring-your-own-key requests bypass the cap. Counters persist across restarts.
- **`/schema` API endpoint** — structured schema (tables, columns, foreign keys) for the UI's ER
  diagram. CORS enabled for the hosted UI origin.
- **Local connector docs** — point the MCP server at any database for zero-data-egress querying.

### Changed
- README rewritten with the live demo, multi-provider usage, and the local-connector model.
- Dockerfile installs the `providers` extra and binds `$PORT` for the host.

## [0.1.0] — 2026-06-04

Initial build (phases P0–P6).

### Added
- Text-to-SQL agent on LangGraph: schema retrieval, SQL writer, validator, executor, answer
  synthesizer, with a self-correction retry loop.
- Read-only guardrails: SELECT/WITH-only validator, read-only connection, statement timeout, row cap.
- MCP server exposing `list_tables`, `get_schema`, and a guardrailed `run_sql`.
- Eval harness: Chinook gold set and **Spider dev sample — 69.3% strict execution accuracy**;
  two-model accuracy/cost comparison.
- Observability: per-query token cost and optional LangSmith tracing.
- Data copilot: schema ER diagram, profiling, and data-quality checks (`schema`, `profile`, `doctor`).
- FastAPI streaming web demo and a self-contained Dockerfile.
