import { useState } from "react";
import { connectDatabase, getSample } from "@/lib/api";
import type { Schema } from "@/lib/types";

/** Choose what the agent queries: the bundled demo DB, or your own.
 *  Cloud DBs connect in-browser via a read-only connection string (SSRF-guarded server-side);
 *  private/local DBs use the local connector, since no hosted page can reach them. */
export default function DataSourcePicker({
  dbUrl,
  onDemo,
  onConnected,
}: {
  dbUrl: string | null;
  onDemo: () => void;
  onConnected: (url: string, schema: Schema) => void;
}) {
  const [tab, setTab] = useState<"demo" | "custom">(dbUrl ? "custom" : "demo");
  const [url, setUrl] = useState(dbUrl ?? "");
  const [state, setState] = useState<"idle" | "connecting" | "error">("idle");
  const [error, setError] = useState("");
  const [showLocal, setShowLocal] = useState(false);

  async function connect() {
    if (!url.trim()) return;
    setState("connecting");
    setError("");
    try {
      const schema = await connectDatabase(url.trim());
      setState("idle");
      onConnected(url.trim(), schema);
    } catch (e) {
      setState("error");
      setError(e instanceof Error ? e.message : "connection failed");
    }
  }

  async function trySample() {
    setState("connecting");
    setError("");
    try {
      const { database_url, schema } = await getSample();
      setUrl(database_url);
      setState("idle");
      onConnected(database_url, schema);
    } catch (e) {
      setState("error");
      setError(e instanceof Error ? e.message : "sample unavailable");
    }
  }

  return (
    <div className="framed" style={{ padding: "16px 16px 14px" }}>
      <span className="framed-tab">data source</span>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => { setTab("demo"); onDemo(); }} aria-pressed={tab === "demo"} style={chip(tab === "demo")}>
          Demo · Chinook
        </button>
        <button onClick={() => setTab("custom")} aria-pressed={tab === "custom"} style={chip(tab === "custom")}>
          Your database
          {dbUrl && <span style={{ color: "var(--ok)", marginLeft: 8 }}>● connected</span>}
        </button>
      </div>

      {tab === "custom" && (
        <div className="reveal" style={{ marginTop: 12 }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            <input
              aria-label="connection string"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && connect()}
              placeholder="postgresql://readonly_user:••••@host:5432/dbname"
              style={{ flex: "1 1 280px", padding: "9px 11px", fontSize: 13 }}
              spellCheck={false}
              autoComplete="off"
            />
            <button
              onClick={connect}
              disabled={state === "connecting" || !url.trim()}
              style={{ padding: "9px 16px", fontSize: 13, fontWeight: 600, background: "var(--line-strong)", color: "var(--paper-panel)", borderColor: "var(--line-strong)" }}
            >
              {state === "connecting" ? "connecting…" : "connect"}
            </button>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 8 }}>
            <button onClick={trySample} disabled={state === "connecting"} style={{ padding: "6px 12px", fontSize: 12.5 }}>
              {state === "connecting" ? "connecting…" : "Try a sample database →"}
            </button>
            <span className="prose" style={{ fontSize: 12, color: "var(--ink-muted)" }}>
              no database of your own? connect a read-only sample
            </span>
          </div>
          <p className="prose" style={{ fontSize: 12, color: "var(--ink-muted)", margin: "8px 0 0", lineHeight: 1.5 }}>
            Postgres or MySQL reachable from the internet. <strong style={{ color: "var(--ink)" }}>Use a read-only user</strong> — queries are
            SELECT-only, but a read-only login is your real guarantee. The string is used per request and not stored.
          </p>
          {state === "error" && (
            <p style={{ fontSize: 12.5, color: "var(--danger)", margin: "8px 0 0" }}>{error}</p>
          )}

          <button
            onClick={() => setShowLocal((s) => !s)}
            style={{ marginTop: 12, padding: "5px 0", border: "none", background: "transparent", color: "var(--ink-muted)", fontSize: 12, textDecoration: "underline", textUnderlineOffset: 3 }}
          >
            {showLocal ? "▾" : "▸"} Database on your laptop or private network?
          </button>
          {showLocal && (
            <div className="reveal" style={{ marginTop: 8 }}>
              <p className="prose" style={{ fontSize: 12.5, color: "var(--ink-muted)", lineHeight: 1.55, margin: "0 0 8px" }}>
                A hosted page can&apos;t reach a database behind your firewall. Run the connector where the
                data lives, so nothing leaves your machine:
              </p>
              <pre style={{ margin: 0, padding: "11px 13px", background: "var(--paper)", border: "1px solid var(--line)", borderRadius: 3, fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: 1.65, overflowX: "auto", color: "var(--ink)" }}>
{`pipx install git+https://github.com/IdoCohen560/promptdb
export PROMPTDB_DATABASE_URL="postgresql://readonly@localhost/mydb"
promptdb ask "top 5 customers by revenue"
# or plug promptdb-mcp into Claude Desktop — see docs/CONNECTOR.md`}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function chip(on: boolean): React.CSSProperties {
  return {
    padding: "7px 13px",
    fontSize: 13,
    background: on ? "var(--line-strong)" : "transparent",
    color: on ? "var(--paper-panel)" : "var(--ink)",
    borderColor: on ? "var(--line-strong)" : "var(--line)",
  };
}
