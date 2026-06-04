# PromptDB — Build Plan

*A production text-to-SQL agent. Ask your database in English.*

**Locked:** 2026-06-04 · **Goal:** get hired as an AI/agent engineer + learn the LangGraph stack deeply · **Constraint:** non-marketing, no startup IP.

## One-liner
A LangGraph agent that answers natural-language questions about a SQL database: it
plans, writes SQL, executes it against a **read-only** connection, recovers from its
own errors in a loop, and explains the result — shipped with an **eval harness**
(measured on the Spider benchmark), **LangSmith observability**, **cost tracking**,
**guardrails**, and a **deployed streaming demo**.

> The resume line is "talk to your database in English." Every hiring manager
> recognizes it instantly and every company wants it.

## Scope (locked 2026-06-04)
**In — Core + read-only "data copilot" features:**
- Core: text-to-SQL Q&A, self-correction loop, read-only guardrails, evals, observability, MCP, CLI.
- **Schema understanding → ER diagram.** DB introspection → render as Mermaid/Graphviz (CLI)
  or Cytoscape/vis.js (web). Deterministic from foreign-key metadata — **not RAG, not graphify**
  (graphify is a code-graph tool; wrong fit). RAG's role stays retrieving relevant tables for
  large schemas (`schema_index`).
- **Analytics / profiling.** Row counts, null rates, cardinality, value distributions, date ranges —
  a "point it at any DB, get an instant data dictionary + profile" command.
- **Data-quality detection (3a).** Surface issues (orphaned FKs, unexpected nulls, duplicate keys,
  type anomalies) as a read-only report.

**Out — explicitly do NOT build:**
- **Write mode / auto-fix (3b).** No agent capability to modify data. The agent stays **strictly
  read-only** — this preserves the OWASP LLM06 least-privilege signal rather than diluting it.
  If ever revisited, only behind dry-run preview + human approval + transaction rollback on a
  disposable DB. Not now.

## Why this gets the callback (each part → a 2026 hiring signal)
| Component | Hiring signal it proves |
|---|---|
| Spider execution-accuracy number + failure-mode breakdown | **Eval design — the #1 signal** |
| LangSmith traces + per-query cost dashboard | **Observability + cost optimization** |
| Self-correcting SQL loop, conditional edges | **Agent orchestration + error recovery** |
| Read-only conn, SELECT-only allow-list, query timeout | **OWASP LLM06 (excessive agency) — senior differentiator** |
| Schema RAG for large DBs | **Vector DB / RAG architecture** |
| FastAPI + Docker + CI eval regression + live URL | **Delivery evidence — "this person ships"** |
| 2-model accuracy/cost comparison in evals | **Frontier-model fluency + cost modeling** |
| DB tools packaged as an MCP server, consumed by the agent via MCP client | **MCP integration (fastest-growing 2026 skill)** |
| Optional: sandboxed browser driving a web SQL console via vision | **Computer-use deployment (senior+ differentiator)** |

One repo, **all 10** differentiated skills (computer-use via the optional stretch phase).

## Architecture — LangGraph node graph
**State** (typed): `question, schema_context, plan, candidate_sql, result, error,
attempts, final_answer, cost_usd`.

Nodes:
1. `schema_retriever` — load table schemas. Small DB: load all. Large DB: embed
   table/column descriptions, retrieve top-k relevant tables (the RAG component).
2. `planner` — identify tables/joins/aggregations needed.
3. `sql_writer` — generate candidate SQL (structured output).
4. `sql_validator` — **guardrail**: valid SQL? read-only (block DROP/DELETE/UPDATE/INSERT)?
   columns real? Reject before execution.
5. `sql_executor` — run on read-only connection, capture rows OR error.
6. **conditional edge** — success → synthesizer; error & attempts<N → back to `sql_writer`
   with the error text (self-correction); attempts≥N → graceful-failure node.
7. `answer_synthesizer` — natural-language answer + the SQL used + the rows.
8. `critic` (optional) — faithfulness check: does the answer match the result set?

**Checkpointer** (SQLite dev / Postgres prod) → enables human-in-the-loop interrupt
before running ambiguous/expensive queries (absorbs the "approval agent" signal too).

**Interfaces — CLI is the flagship.** The reusable unit is an importable `agent` core
library (graph + DB tools). The **CLI (`promptdb "question"`) is the primary product and
reference UX** — it's the headline of the README and the main demo. The **MCP server** and
**FastAPI + web UI** are secondary adapters that **import the same `agent` core**.
**Rule:** secondary interfaces import the core; they never subprocess the CLI binary
(that would break streaming, add latency, and hurt testability). CLI-first, library-clean.

**MCP layer:** the DB tools (`run_sql`, `get_schema`, `list_tables`) live in a standalone
**MCP server**. The LangGraph agent consumes them via an **MCP client** rather than
calling Python functions directly. Proves both authoring + consuming MCP, and lets an
interviewer plug the server into Claude Desktop to use the DB live.

**Computer-use path (optional stretch):** a second executor where, instead of a direct DB
connection, the agent drives a **sandboxed browser** (Playwright in Docker) to a web SQL
console — types SQL, reads the result from a screenshot via a vision model. Same agent,
two execution modes (tool-calling vs vision-action) → you can demo and compare them.

## Eval harness (build this EARLY — it's the point)
- Dataset: **Spider** dev subset (~100–200 Qs) to start → stretch goal **BIRD-SQL**
  (harder, more realistic, more impressive).
- Metrics: **execution accuracy** (my result == gold result), exact-set-match, latency
  p50/p95, **cost per query**.
- Failure-mode analysis: bucket failures (joins / aggregations / nested / ambiguity) —
  this is the "failure-mode discussion" interviewers screen for.
- Run in **GitHub Actions** on every push → regression tracking.
- Tooling: LangSmith datasets + evaluators (or DeepEval / custom).

## Observability & cost
- LangSmith tracing on every node (be able to explain traces vs spans).
- Cost tracker: tokens × model price → **cost-per-query**, logged + dashboarded.
- Compare 2 models (e.g. Claude Sonnet vs a cheaper model) on accuracy *and* cost.

## Deployment
- FastAPI `/query` endpoint; rate limiting, API-key auth, structured logging w/ trace IDs.
- Streamlit (or Next) UI: type a question, **stream the agent's steps live**, show
  SQL + rows + answer. This is the demo that photographs well.
- Docker → Railway / Fly.io / Render. Public GitHub repo with architecture diagram + eval table in README.

## Stack
Python 3.11+, LangGraph + LangChain, Anthropic (Claude) primary LLM, SQLite +
sample analytics DB (Chinook to start, then Spider DBs), Postgres checkpointer in prod,
LangSmith, FastAPI, Streamlit, Docker, GitHub Actions.

## Repo structure
```
promptdb/
  README.md            # diagram, eval results table, demo gif/link
  pyproject.toml
  src/
    agent/ graph.py state.py nodes/ guardrails.py prompts/   # importable core (the reusable unit)
    cli/ main.py                          # FLAGSHIP interface: `promptdb "question"`
    db/ connection.py schema_index.py
    data/ schema_graph.py profile.py quality.py   # Tier 2: ER diagram, profiling, data-quality (all read-only)
    mcp_server/ server.py tools.py        # secondary adapter — imports agent core
    browser/ computer_use.py              # optional: sandboxed vision-action executor
    api/ main.py                          # secondary adapter — imports agent core
    observability/ cost.py tracing.py
  evals/ dataset.py run_evals.py evaluators.py results/
  app/ streamlit_app.py
  tests/
  docker/
  .github/workflows/evals.yml
```

## Phased milestones (each independently demo-able)
- **P0 Setup** → verify: env runs, deps pinned, **current LangGraph docs read** (training may be stale on import paths — confirm before coding).
- **P1 Happy path** → verify: agent correctly answers a simple question on Chinook end-to-end.
- **P2 Self-correction + guardrails** → verify: an error-inducing question recovers within N retries; a `DELETE` is blocked by the validator.
- **P2.5 MCP layer** → verify: DB tools run as an MCP server; agent calls them via MCP client; server plugs into Claude Desktop and answers a query live.
- **P3 Eval harness** → verify: a real execution-accuracy % on Spider subset + failure-mode table; CI runs evals on push.
- **P4 Observability + cost** → verify: LangSmith traces visible; cost-per-query logged; 2-model comparison table.
- **P4.5 Data copilot (Tier 2, read-only)** → verify three commands work on Chinook:
  `promptdb schema` renders an ER diagram; `promptdb profile` outputs a data dictionary
  (row counts, null rates, distributions); `promptdb doctor` reports data-quality issues
  (orphaned FKs, dupes, nulls). All read-only.
- **P5 Deploy + UI** → verify: live URL, streaming steps, schema diagram + profile shown, screenshots mobile/desktop.
- **P6 README + resume** → verify: README has diagram + eval table + demo link; resume bullet drafted.
- **P7 Computer-use (optional stretch)** → verify: agent answers a question by driving a sandboxed browser to a web SQL console (vision-action), with the tool-calling path still available for comparison.

## Resume bullet (real numbers)
> Built **PromptDB**, a production text-to-SQL agent (LangGraph) reaching **69.3% execution
> accuracy on a 150-question Spider dev sample**; self-correcting query loop, read-only SQL
> guardrails (OWASP LLM06), an MCP server, LangSmith tracing, **~$0.005 cost-per-query**
> tracking, and a CI eval suite; FastAPI + Docker streaming web demo.

## Open decisions (none blocking)
- **Model:** Claude (recommended, your ecosystem, strong SQL) — but compare against a cheaper model in evals for the cost story.
- **Benchmark:** start Spider → stretch BIRD.
- **UNCERTAINTY — exact LangGraph API:** import paths / method names change between
  versions and my training may be stale. *Resolved at P0 by reading current docs before
  writing any node.* This is the one thing I will not guess.

## Demo experience (designed in from day 1, not bolted on)
The demo is the deliverable that converts the repo into a callback. The CLI is the
flagship demo surface; the web demo is secondary. All driven by the same agent core:

1. **CLI demo (primary / flagship).** `promptdb "which 5 artists earned the most?"` —
   the terminal **streams the agent's steps live**: `planning → wrote SQL → query failed,
   retrying → success → answer`, prints the generated SQL, the result table, the plain-English
   answer, and a **latency + cost** footer. Recorded as an asciinema GIF at the top of the
   README. Fastest, cleanest "wow" — no UI needed, and the self-correction step is visible.
2. **Live web demo (secondary).** A hosted URL wrapping the same core: pick a sample DB
   (Chinook / e-commerce) or connect a read-only DB, ask a question, watch the same live
   stream in a browser with the SQL in a code box and result as a table.
3. **60-second video walkthrough** (for LinkedIn / portfolio / application). Script below.
4. **The repo itself** — README opens with an architecture diagram, the **Spider eval
   results table** (the hard accuracy number), the CLI GIF, and the live link.

**Sample questions that show off the agent in a demo** (Chinook DB):
- "Which 5 artists earned the most revenue?" (joins + aggregation + sort)
- "What's the average invoice total by country, only countries with 10+ customers?" (group + having)
- "Show me customers who bought a track but never a full album." (the hard one — nested logic; great if it nails it, great failure-mode story if it doesn't)
- A deliberately ambiguous one to show the human-in-the-loop pause.

**60-second demo script (record at P5):**
- 0–10s: "Most companies can't let non-technical staff query their data. This agent fixes that — ask in English." Type question, hit go.
- 10–35s: Narrate the live stream — "watch it plan, write SQL, the query errors on a bad join, and it *reads the error and rewrites itself* — that loop is the whole point."
- 35–50s: Show the answer + the SQL + the cost-per-query footer. "Every run is traced in LangSmith and costs about $0.00Y."
- 50–60s: Cut to the README eval table. "Measured: X% execution accuracy on the Spider benchmark across 200 questions, with a failure-mode breakdown." End on the live URL.

**Demoability is gated in the phases:** P1 already produces a runnable CLI demo; P5
produces the hosted streaming UI; P6 produces the video + README GIF. There is a
demo-able artifact at the end of *every* phase — never a long dark stretch.

## Estimated effort
~2–4 weekends part-time, phased so every phase is a standalone demo.
