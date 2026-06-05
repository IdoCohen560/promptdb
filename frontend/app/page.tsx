"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import SchemaBlueprint from "@/components/SchemaBlueprint";
import FlowRail, { type StageStatus } from "@/components/FlowRail";
import ResultTable from "@/components/ResultTable";
import ProviderPicker from "@/components/ProviderPicker";
import DataSourcePicker from "@/components/DataSourcePicker";
import { getSample, getUsage, postQuery } from "@/lib/api";
import { STAGES, type Byo, type QueryResult, type Schema, type StageNode, type Usage } from "@/lib/types";

const FIRESCOPE_SITE = "https://firescope.netlify.app";

const EXAMPLES = [
  "how many news articles were published each month?",
  "how many news articles are there per category?",
  "how many users are registered, grouped by role?",
  "how many distinct days have published articles?",
];

// schema-agnostic starters for a connected user database
const CUSTOM_EXAMPLES = [
  "how many rows are in each table?",
  "list the tables and their row counts",
  "what columns does the largest table have?",
];

const ALL_PENDING = (): Record<StageNode, StageStatus> =>
  Object.fromEntries(STAGES.map((s) => [s.node, "pending"])) as Record<StageNode, StageStatus>;
const ALL_DONE = (): Record<StageNode, StageStatus> =>
  Object.fromEntries(STAGES.map((s) => [s.node, "done"])) as Record<StageNode, StageStatus>;

// A real, pre-computed run against the FireScope demo DB, shown on load so visitors see the agent
// working instantly (no cost). Replaced the moment they run something live.
const DEMO_EXAMPLE: QueryResult = {
  question: "how many news articles were published each month?",
  sql: "SELECT DATE_TRUNC('month', published_at)::DATE AS month, COUNT(*) AS count\nFROM news_articles\nWHERE published_at IS NOT NULL\nGROUP BY DATE_TRUNC('month', published_at)\nORDER BY month DESC\nLIMIT 6",
  columns: ["month", "count"],
  rows: [["2026-06-01", 17], ["2026-05-01", 156], ["2026-04-01", 58], ["2026-03-01", 14]],
  answer: "May 2026 saw the most wildfire coverage with 156 articles, ahead of April (58), June (17), and March (14). The agent read the schema, wrote this read-only PostgreSQL query, ran it, and explained the result.",
  error: null,
  cost_usd: 0.0031,
  latency_s: 2.4,
  usage: null,
};

export default function Page() {
  const [schema, setSchema] = useState<Schema | null>(null);   // the FireScope demo schema
  const [usage, setUsage] = useState<Usage | null>(null);
  const [question, setQuestion] = useState("");
  const [byo, setByo] = useState<Byo>(null);
  const [source, setSource] = useState<"demo" | "custom">("demo");
  const [dbUrl, setDbUrl] = useState<string | null>(null);     // a connected user database (custom mode)
  const [customSchema, setCustomSchema] = useState<Schema | null>(null);  // connected DB's schema
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<Record<StageNode, StageStatus>>(ALL_DONE);
  const [attempts, setAttempts] = useState(1);
  const [result, setResult] = useState<QueryResult | null>(DEMO_EXAMPLE);
  const [isExample, setIsExample] = useState(true);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    getSample().then(setSchema).catch(() => setNotice("Could not reach the demo database."));
    getUsage().then(setUsage).catch(() => {});
  }, []);

  const inDemo = source === "demo";
  const effectiveSchema = inDemo ? schema : customSchema;  // demo → FireScope; custom → connected DB

  const activeTables = useMemo(() => {
    if (!effectiveSchema || !result?.sql) return [];
    const s = result.sql.toLowerCase();
    return effectiveSchema.tables.filter((t) => s.includes(t.name.toLowerCase())).map((t) => t.name);
  }, [effectiveSchema, result?.sql]);

  const advance = useCallback((doneNode: StageNode) => {
    setStatus((prev) => {
      const next = { ...prev };
      next[doneNode] = "done";
      const idx = STAGES.findIndex((s) => s.node === doneNode);
      if (idx + 1 < STAGES.length) next[STAGES[idx + 1].node] = "active";
      return next;
    });
  }, []);

  const run = useCallback(
    async (q: string, ctx?: { source: "demo" | "custom"; dbUrl: string | null }) => {
      const src = ctx?.source ?? source;       // override lets onConnected run before state settles
      const url = ctx?.dbUrl ?? dbUrl;
      if (!q.trim() || running) return;
      if (src === "custom" && !url) {
        setNotice("Connect a database first, or switch to the FireScope demo.");
        return;
      }
      setRunning(true);
      setIsExample(false);
      setNotice(null);
      setResult(null);
      setAttempts(1);
      setStatus({ ...ALL_PENDING(), schema_retriever: "active" });
      try {
        const res = await postQuery(q, byo, src === "custom" ? url : null, src === "demo");
        for (let i = 0; i < STAGES.length; i++) {
          await new Promise((r) => setTimeout(r, 150));
          advance(STAGES[i].node);
        }
        setResult(res);
        if (res.usage) setUsage(res.usage);
      } catch (e) {
        setStatus(ALL_PENDING());
        setNotice(e instanceof Error ? e.message : "Query failed.");
      } finally {
        setRunning(false);
      }
    },
    [byo, dbUrl, source, running, advance],
  );

  const placeholder = inDemo ? EXAMPLES[0] : "ask your connected database…";

  return (
    <main style={{ maxWidth: 1080, margin: "0 auto", padding: "clamp(28px, 5vw, 64px) clamp(18px, 4vw, 40px) 80px" }}>
      <Header usage={usage} inDemo={inDemo} />

      <section style={{ marginTop: 40 }}>
        <QueryBar question={question} setQuestion={setQuestion} onRun={run} running={running} placeholder={placeholder} />
        {!running && (inDemo || dbUrl) && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 14, alignItems: "center" }}>
            <span className="label" style={{ marginRight: 2 }}>try live →</span>
            {(inDemo ? EXAMPLES : CUSTOM_EXAMPLES).map((ex) => (
              <button key={ex} onClick={() => { setQuestion(ex); run(ex); }} style={{ padding: "6px 11px", fontSize: 12.5, color: "var(--ink)" }}>
                {ex}
              </button>
            ))}
          </div>
        )}
      </section>

      <section style={{ marginTop: 18, display: "grid", gap: 18, gridTemplateColumns: "minmax(0, 1fr)" }}>
        <DataSourcePicker
          source={source}
          onDemo={() => {
            setSource("demo"); setDbUrl(null); setResult(DEMO_EXAMPLE);
            setIsExample(true); setStatus(ALL_DONE()); setSelectedTable(null); setNotice(null);
          }}
          onCustom={() => { setSource("custom"); setDbUrl(null); setCustomSchema(null); setResult(null); setIsExample(false); setSelectedTable(null); }}
          onConnected={(url, sch) => {
            setSource("custom"); setDbUrl(url); setCustomSchema(sch); setSelectedTable(null);
            // fast worked example: count one real table (single query, not a 14-table union)
            const starter = sch.tables[0]
              ? `how many rows are in the ${sch.tables[0].name} table?`
              : "how many tables are in this database?";
            run(starter, { source: "custom", dbUrl: url });
          }}
        />
        <ProviderPicker byo={byo} setByo={setByo} usage={usage} />
      </section>

      {notice && (
        <div className="panel reveal" style={{ marginTop: 20, padding: "12px 16px", borderColor: "var(--danger)", display: "flex", gap: 10, alignItems: "baseline" }}>
          <span style={{ color: "var(--danger)", fontWeight: 600, fontSize: 12 }}>NOTICE</span>
          <span style={{ fontSize: 13.5 }}>{notice}</span>
        </div>
      )}

      {(running || result) && (
        <section className="framed reveal" style={{ marginTop: 28, padding: "20px 20px 22px" }}>
          <span className="framed-tab">{isExample ? "example" : "pipeline"}</span>
          {isExample && (
            <p className="prose" style={{ margin: "0 0 14px", fontSize: 13, color: "var(--ink-muted)" }}>
              A worked example on the <a href={FIRESCOPE_SITE} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline", textUnderlineOffset: 2 }}>FireScope</a> wildfire database.
              Edit the question above (or click a chip) and hit <strong style={{ color: "var(--ink)" }}>run</strong> to query live.
            </p>
          )}
          <FlowRail status={status} attempts={attempts} />

          {result?.sql && (
            <div className="reveal" style={{ marginTop: 22 }}>
              <div className="label" style={{ marginBottom: 7, display: "flex", gap: 10, alignItems: "center" }}>
                generated SQL
                <span style={{ color: "var(--ok)", border: "1px solid var(--ok)", borderRadius: 2, padding: "0 5px", fontSize: 9.5 }}>READ-ONLY</span>
              </div>
              <pre style={{ margin: 0, padding: "13px 15px", background: "var(--paper)", border: "1px solid var(--line)", borderRadius: 3, fontFamily: "var(--font-mono)", fontSize: 13, lineHeight: 1.6, overflowX: "auto", color: "var(--ink)" }}>
                {result.sql}
              </pre>
            </div>
          )}

          {result?.columns && result.rows && !result.error && (
            <div className="reveal" style={{ marginTop: 20 }}>
              <div className="label" style={{ marginBottom: 7 }}>result · {result.rows.length} row{result.rows.length === 1 ? "" : "s"}</div>
              <ResultTable columns={result.columns} rows={result.rows} />
            </div>
          )}

          {result?.answer && (
            <p className="prose reveal" style={{ marginTop: 22, fontSize: 16, lineHeight: 1.6, maxWidth: "68ch", color: "var(--ink)" }}>{result.answer}</p>
          )}

          {result && result.cost_usd != null && (
            <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid var(--grid)", display: "flex", gap: 20, flexWrap: "wrap", fontSize: 12, color: "var(--ink-muted)" }}>
              <span>cost ${(result.cost_usd ?? 0).toFixed(5)}</span>
              {result.latency_s != null && <span>latency {result.latency_s}s</span>}
              {byo ? <span>model {byo.model}</span> : <span>demo · {usage?.free_queries_left ?? "—"} free left</span>}
            </div>
          )}
        </section>
      )}

      {effectiveSchema && (
        <section style={{ marginTop: 28 }}>
          <div className="framed" style={{ padding: "18px 18px 20px" }}>
            <span className="framed-tab">
              {inDemo ? "demo · FireScope wildfire" : "your database"} · {effectiveSchema.tables.length} tables
            </span>
            <p className="prose" style={{ fontSize: 12, color: "var(--ink-muted)", margin: "0 0 12px" }}>
              Hover a table to trace its relationships · click to inspect every column
              {inDemo && <>{" · "}<a href={FIRESCOPE_SITE} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline", textUnderlineOffset: 2 }}>see the live FireScope project →</a></>}
            </p>
            <SchemaBlueprint schema={effectiveSchema} dimmed={running} active={activeTables} selected={selectedTable} onSelect={(t) => setSelectedTable((s) => (s === t ? null : t))} />
            {selectedTable && (() => {
              const t = effectiveSchema.tables.find((x) => x.name === selectedTable);
              if (!t) return null;
              return (
                <div className="reveal" style={{ marginTop: 14, borderTop: "1px solid var(--line)", paddingTop: 14 }}>
                  <div className="label" style={{ marginBottom: 9, display: "flex", gap: 10, alignItems: "center" }}>
                    <span style={{ color: "var(--data-strong)" }}>{t.name}</span> · {t.columns.length} columns
                    <button onClick={() => setSelectedTable(null)} style={{ marginLeft: "auto", padding: "2px 8px", fontSize: 11 }}>close</button>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "0 18px" }}>
                    {t.columns.map((c) => (
                      <div key={c.name} style={{ display: "flex", justifyContent: "space-between", gap: 10, fontFamily: "var(--font-mono)", fontSize: 12.5, padding: "4px 0", borderBottom: "1px solid var(--grid)" }}>
                        <span style={{ color: "var(--ink)", fontWeight: c.pk ? 600 : 400 }}>
                          {c.name}{c.pk && <span style={{ color: "var(--data-strong)", fontSize: 9, marginLeft: 5, letterSpacing: "0.08em" }}>PK</span>}
                        </span>
                        <span style={{ color: "var(--ink-muted)" }}>{c.type}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </section>
      )}

      <Footer />
    </main>
  );
}

function Header({ usage, inDemo }: { usage: Usage | null; inDemo: boolean }) {
  return (
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
      <div>
        <h1 style={{ fontFamily: "var(--font-mono)", fontSize: "clamp(26px, 4vw, 38px)", fontWeight: 600, letterSpacing: "-0.01em", color: "var(--ink)" }}>PromptDB</h1>
        <p className="prose" style={{ marginTop: 8, fontSize: 15.5, color: "var(--ink-muted)", maxWidth: "54ch", lineHeight: 1.5 }}>
          Ask a database in plain English. The agent reads the schema, writes a read-only query,
          self-corrects, runs it, and explains the answer.
        </p>
      </div>
      <div className="mono" style={{ textAlign: "right", fontSize: 12, color: "var(--ink-muted)", lineHeight: 1.7, flexShrink: 0 }}>
        <div>69.3% · Spider dev</div>
        <div>read-only · self-correcting</div>
        {inDemo && usage && <div style={{ color: usage.demo_open ? "var(--ok)" : "var(--danger)" }}>● demo {usage.demo_open ? "open" : "capped"}</div>}
      </div>
    </header>
  );
}

function QueryBar({
  question, setQuestion, onRun, running, placeholder,
}: { question: string; setQuestion: (s: string) => void; onRun: (q: string) => void; running: boolean; placeholder: string }) {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onRun(question); }} className="framed" style={{ display: "flex", alignItems: "center", padding: "4px 4px 4px 16px", gap: 10 }}>
      <span className="framed-tab">ask</span>
      <span className="caret mono" style={{ fontSize: 18, lineHeight: 1 }}>▏</span>
      <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={placeholder} aria-label="question" style={{ flex: 1, border: "none", background: "transparent", padding: "12px 0", fontSize: 16, boxShadow: "none" }} disabled={running} />
      <button type="submit" disabled={running || !question.trim()} style={{ padding: "11px 20px", fontSize: 14, fontWeight: 600, background: running ? "transparent" : "var(--line-strong)", color: running ? "var(--ink-muted)" : "var(--paper-panel)", borderColor: "var(--line-strong)" }}>
        {running ? "running…" : "run"}
      </button>
    </form>
  );
}

function Footer() {
  return (
    <footer className="prose" style={{ marginTop: 56, paddingTop: 20, borderTop: "1px solid var(--grid)", fontSize: 12.5, color: "var(--ink-muted)", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
      <span>Demo data from the <a href={FIRESCOPE_SITE} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline", textUnderlineOffset: 3 }}>FireScope</a> wildfire project · query your own database with zero data egress.</span>
      <a href="https://github.com/IdoCohen560/promptdb" style={{ color: "var(--ink)", textDecoration: "underline", textUnderlineOffset: 3 }}>github.com/IdoCohen560/promptdb</a>
    </footer>
  );
}
