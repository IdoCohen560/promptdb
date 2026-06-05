import { useState } from "react";
import { connectDatabase } from "@/lib/api";

const FIRESCOPE_SITE = "https://firescope.netlify.app";

/** Choose what the agent queries: the FireScope wildfire demo, or your own database.
 *  Cloud DBs connect in-browser via a read-only connection string (SSRF-guarded server-side);
 *  private/local DBs use the local connector, since no hosted page can reach them. */
export default function DataSourcePicker({
  source,
  onDemo,
  onCustom,
  onConnected,
}: {
  source: "demo" | "custom";
  onDemo: () => void;
  onCustom: () => void;
  onConnected: (url: string) => void;
}) {
  const [url, setUrl] = useState("");
  const [state, setState] = useState<"idle" | "connecting" | "error">("idle");
  const [error, setError] = useState("");
  const [showLocal, setShowLocal] = useState(false);

  async function connect() {
    if (!url.trim()) return;
    setState("connecting");
    setError("");
    try {
      await connectDatabase(url.trim()); // validates + SSRF-checks server-side
      setState("idle");
      onConnected(url.trim());
    } catch (e) {
      setState("error");
      setError(e instanceof Error ? e.message : "connection failed");
    }
  }

  return (
    <div className="framed" style={{ padding: "16px 16px 14px" }}>
      <span className="framed-tab">data source</span>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={onDemo} aria-pressed={source === "demo"} style={chip(source === "demo")}>Demo · FireScope</button>
        <button onClick={onCustom} aria-pressed={source === "custom"} style={chip(source === "custom")}>Your database</button>
      </div>

      {source === "demo" && (
        <p className="prose" style={{ fontSize: 12, color: "var(--ink-muted)", margin: "10px 0 0", lineHeight: 1.5 }}>
          Read-only queries against the{" "}
          <a href={FIRESCOPE_SITE} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline", textUnderlineOffset: 2 }}>FireScope</a>{" "}
          wildfire database — a real project, served read-only on the demo key.
        </p>
      )}

      {source === "custom" && (
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
            <button onClick={connect} disabled={state === "connecting" || !url.trim()} style={{ padding: "9px 16px", fontSize: 13, fontWeight: 600, background: "var(--line-strong)", color: "var(--paper-panel)", borderColor: "var(--line-strong)" }}>
              {state === "connecting" ? "connecting…" : "connect"}
            </button>
          </div>
          <p className="prose" style={{ fontSize: 12, color: "var(--ink-muted)", margin: "8px 0 0", lineHeight: 1.5 }}>
            Postgres or MySQL reachable from the internet. <strong style={{ color: "var(--ink)" }}>Use a read-only user</strong> — queries are
            SELECT-only, but a read-only login is your real guarantee. The string is used per request and not stored.
          </p>
          {state === "error" && <p style={{ fontSize: 12.5, color: "var(--danger)", margin: "8px 0 0" }}>{error}</p>}

          <button onClick={() => setShowLocal((s) => !s)} style={{ marginTop: 12, padding: "5px 0", border: "none", background: "transparent", color: "var(--ink-muted)", fontSize: 12, textDecoration: "underline", textUnderlineOffset: 3 }}>
            {showLocal ? "▾" : "▸"} Database on your laptop or private network?
          </button>
          {showLocal && (
            <div className="reveal" style={{ marginTop: 8 }}>
              <p className="prose" style={{ fontSize: 12.5, color: "var(--ink-muted)", lineHeight: 1.55, margin: "0 0 8px" }}>
                A hosted page can&apos;t reach a database behind your firewall. Run the connector where the data lives, so nothing leaves your machine:
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
