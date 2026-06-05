import type { Byo, Provider, Usage } from "@/lib/types";

const PROVIDERS: { id: Provider; label: string; placeholder: string; defaultModel: string; keyless?: boolean }[] = [
  { id: "anthropic", label: "Anthropic", placeholder: "sk-ant-…", defaultModel: "claude-sonnet-4-6" },
  { id: "openai", label: "OpenAI", placeholder: "sk-…", defaultModel: "gpt-4o-mini" },
  { id: "ollama", label: "Ollama (local)", placeholder: "no key — runs on your machine", defaultModel: "gemma2", keyless: true },
];

/** Demo (server key, N free queries) vs bring-your-own model. The key lives only in this
 *  component's state and the request body, never persisted. */
export default function ModelPicker({
  byo,
  setByo,
  usage,
}: {
  byo: Byo;
  setByo: (b: Byo) => void;
  usage: Usage | null;
}) {
  const active = byo?.provider ?? null;
  const current = PROVIDERS.find((p) => p.id === active);

  function choose(id: Provider | null) {
    if (id === null) return setByo(null);
    const p = PROVIDERS.find((x) => x.id === id)!;
    setByo({ provider: id, model: p.defaultModel, apiKey: "" });
  }

  return (
    <div className="framed" style={{ padding: "16px 16px 14px" }}>
      <span className="framed-tab">model</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <button
          onClick={() => choose(null)}
          aria-pressed={active === null}
          style={chip(active === null)}
        >
          Demo key
          {usage && (
            <span style={{ color: active === null ? "var(--paper-panel)" : "var(--ink-muted)", marginLeft: 8 }}>
              {usage.free_queries_left} free
            </span>
          )}
        </button>
        {PROVIDERS.map((p) => (
          <button
            key={p.id}
            onClick={() => choose(p.id)}
            aria-pressed={active === p.id}
            style={chip(active === p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {current && (
        <div className="reveal" style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12 }}>
          <input
            aria-label="model name"
            value={byo!.model}
            onChange={(e) => setByo({ ...byo!, model: e.target.value })}
            style={{ flex: "1 1 160px", padding: "8px 10px", fontSize: 13 }}
            placeholder={current.defaultModel}
          />
          {!current.keyless && (
            <input
              aria-label="api key"
              type="password"
              value={byo!.apiKey}
              onChange={(e) => setByo({ ...byo!, apiKey: e.target.value })}
              style={{ flex: "2 1 220px", padding: "8px 10px", fontSize: 13 }}
              placeholder={current.placeholder}
              autoComplete="off"
            />
          )}
          <p
            className="prose"
            style={{ flexBasis: "100%", fontSize: 12, color: "var(--ink-muted)", margin: "2px 0 0" }}
          >
            {current.keyless
              ? "Runs against an Ollama server on your machine. Start the local connector first."
              : "Your key is sent only with the request and never stored."}
          </p>
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
