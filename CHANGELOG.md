# Changelog

All notable changes to PromptDB are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Live hosted demo** at [promptdb-ai.vercel.app](https://promptdb-ai.vercel.app) — Next.js "blueprint"
  UI on Vercel, agent API on Render. Interactive schema (hover to trace foreign keys, click to inspect
  every column), animated result data-bars (GSAP), data-source + model pickers, and a real precomputed
  worked example on arrival.
- **Any model** — any OpenAI-compatible endpoint (OpenRouter → hundreds of models incl. all open-source,
  OpenAI, Anthropic, custom `base_url`). `/models` lists a provider's catalog live. The per-request model
  is injected via LangGraph config, so keys never enter graph state or traces.
- **Connect your own database** — paste a read-only Postgres/MySQL connection string (queried server-side,
  SSRF-guarded) or use the local connector for private DBs. `/connect` validates + introspects; on connect,
  `/suggest` generates starter questions grounded in *your* schema and the first auto-runs.
- **Dialect-aware SQL** — the writer uses PostgreSQL / MySQL / SQLite syntax for the connected engine.
- **Helpful empty results** — a 0-row filtered query surfaces the column's real values ("did you mean…")
  instead of looking broken.
- **FireScope demo database** — the demo runs against a real project's Postgres (14 tables). A table
  allowlist + credential-column guard keep `password_hash` and `SELECT *` on the users table out of results.
- **`/sample`, `/suggest`, `/models`, `/connect`** API endpoints.

### Changed
- **Per-browser demo quota** — free queries are metered per client id (`X-Client-Id`), not per IP, so users
  behind a shared IP each get their own. Global daily spend ceiling unchanged.
- README / ARCHITECTURE / SECURITY updated for the demo, all-models, connect-your-DB, and the new guards.
- Dockerfile installs `providers`, binds `$PORT`, and runs with `--proxy-headers` so the API sees the real
  client IP behind Render's proxy.

### Fixed
- Per-IP rate limiting bucketed all users under the proxy IP (now uses the real client IP).
- Example questions that baited a non-existent filter value (returned 0 rows).
- Empty-result hint helper now respects the credential denylist (defense-in-depth).

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
