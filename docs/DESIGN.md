# PromptDB — Design System

Direction: **Schematic Blueprint with live data**. The interface looks like a technical drawing
the agent reads and annotates. Cool ink-blue structure (schema, linework, flow); warm amber for
live data (result bars, key values). Light, precise, instrument-grade. Never the dark neon "AI" look.

## Theme
Light. Scene: a skeptical senior engineer on a 14" laptop in a bright office, giving it 30 seconds.
The surface reads like drafting paper under good light, not a glowing tool in a dark room.

## Color (OKLCH)
Structure is cool; data is warm. That contrast is the whole identity, hold it.

| Role | OKLCH | Use |
|---|---|---|
| `--paper` | `oklch(0.971 0.008 240)` | page ground (cool blueprint paper) |
| `--paper-panel` | `oklch(0.992 0.004 240)` | raised panels (SQL, results) |
| `--grid` | `oklch(0.93 0.012 240)` | faint blueprint grid lines |
| `--ink` | `oklch(0.27 0.03 252)` | primary text (deep ink, never #000) |
| `--ink-muted` | `oklch(0.52 0.028 252)` | secondary text, labels |
| `--line` | `oklch(0.58 0.10 250)` | blueprint linework, borders, ER edges |
| `--line-strong` | `oklch(0.46 0.13 254)` | emphasized structure, active node |
| `--data` | `oklch(0.77 0.135 70)` | amber data bars, live values |
| `--data-strong` | `oklch(0.68 0.15 64)` | top/peak data value |
| `--ok` | `oklch(0.62 0.10 152)` | read-only guardrail, success ticks |
| `--danger` | `oklch(0.57 0.16 25)` | errors, cap reached |

Color strategy: **Committed**. Cool paper + ink-blue structure carry the surface; amber is the
deliberate ~10–15% data accent. Not Restrained (the blue structure is load-bearing, not a lone accent).

## Typography
- **IBM Plex Mono** — SQL, result tables, schema labels, costs, the input prompt caret. Earned: this is code and data.
- **Inter** — the synthesized answer prose and body copy only. Capped at 68ch.
- Scale ratio ≥1.25. Display (logo/section) in Mono with letter-spacing tightened. Hierarchy by weight (400/500/600) + size, not color alone.

## Layout
- A blueprint grid background (CSS, faint `--grid` lines, ~28px). It IS the container; do not wrap everything in cards.
- The schema ER diagram is the hero on first load: tables as labelled nodes, FKs as ink-blue edges, drawn in SVG. On query, it recedes (dims) as focus moves to the query flow.
- Query flow: english → SQL → rows → answer, laid out as a left-to-right schematic with ink-blue connectors; each stage lights up as it streams (`--line-strong`).
- Result table: monospace, hairline `--line` rules; numeric columns get an inline amber bar scaled to the column max (the warm data against the cool structure). No card nesting.

## Motion
- Stages reveal with opacity + 6px translate, ease-out-expo, ~320ms. Never animate layout props.
- The active flow connector draws in (stroke-dashoffset) as a stage runs. No bounce, no glow pulse.

## Components
- **Schema blueprint** (SVG ER): node = table (mono title + column list, PK marked); edge = FK.
- **Query bar**: a mono input with a `▏` caret motif, blueprint-framed, not a rounded chat box.
- **Flow rail**: 4 stage chips with connectors; tick when done, danger on error + retry count.
- **SQL panel**: framed mono block, read-only badge, copy affordance.
- **Result table**: mono, inline amber bars on numeric columns, row count + latency + cost in the footer.
- **Model picker**: demo (server key, N free left) vs BYO (provider: Anthropic / OpenAI / Ollama + key field). Key stays client-side.

## Bans (in addition to the global impeccable bans)
- No glowing borders, no purple gradients, no robot/chat-bubble mascot.
- No gradient text, no side-stripe accents, no hero-metric template, no identical card grid.
- The schema is drawn as real structure, not faked with decorative lines.
