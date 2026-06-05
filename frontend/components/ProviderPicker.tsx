import { useState } from "react";
import { fetchModels } from "@/lib/api";
import { LISTABLE, type Byo, type Preset, type Usage } from "@/lib/types";

const PRESETS: { id: Preset | "demo"; label: string }[] = [
  { id: "demo", label: "Demo key" },
  { id: "openrouter", label: "OpenRouter" },
  { id: "openai", label: "OpenAI" },
  { id: "anthropic", label: "Anthropic" },
  { id: "custom", label: "Custom" },
];

const DEFAULT_MODEL: Record<Preset, string> = {
  openrouter: "anthropic/claude-3.5-sonnet",
  openai: "gpt-4o-mini",
  anthropic: "claude-sonnet-4-6",
  custom: "",
};

/** Choose the model. Demo uses the server key (N free). Any other choice is bring-your-own on an
 *  OpenAI-compatible endpoint — OpenRouter alone is hundreds of models including all open-source.
 *  Keys live only in this component's state and the request body. */
export default function ProviderPicker({
  byo,
  setByo,
  usage,
}: {
  byo: Byo;
  setByo: (b: Byo) => void;
  usage: Usage | null;
}) {
  const active: Preset | "demo" = byo?.preset ?? "demo";
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  function choose(id: Preset | "demo") {
    setModels([]);
    setErr("");
    if (id === "demo") return setByo(null);
    setByo({ preset: id, baseUrl: "", model: DEFAULT_MODEL[id], apiKey: "" });
  }

  async function loadModels() {
    if (!byo) return;
    setLoading(true);
    setErr("");
    try {
      setModels(await fetchModels(byo));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "could not load models");
    } finally {
      setLoading(false);
    }
  }

  const canList = byo && LISTABLE.includes(byo.preset);

  return (
    <div className="framed" style={{ padding: "16px 16px 14px" }}>
      <span className="framed-tab">model</span>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {PRESETS.map((p) => (
          <button key={p.id} onClick={() => choose(p.id)} aria-pressed={active === p.id} style={chip(active === p.id)}>
            {p.label}
            {p.id === "demo" && usage && (
              <span style={{ color: active === "demo" ? "var(--paper-panel)" : "var(--ink-muted)", marginLeft: 8 }}>
                {usage.free_queries_left} free
              </span>
            )}
          </button>
        ))}
      </div>

      {byo && (
        <div className="reveal" style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {byo.preset === "custom" && (
            <input
              aria-label="base url"
              value={byo.baseUrl}
              onChange={(e) => setByo({ ...byo, baseUrl: e.target.value })}
              placeholder="https://your-endpoint/v1"
              style={{ flexBasis: "100%", padding: "8px 10px", fontSize: 13 }}
              spellCheck={false}
            />
          )}
          <input
            aria-label="api key"
            type="password"
            value={byo.apiKey}
            onChange={(e) => setByo({ ...byo, apiKey: e.target.value })}
            placeholder={byo.preset === "openrouter" ? "sk-or-…" : "API key"}
            style={{ flex: "2 1 200px", padding: "8px 10px", fontSize: 13 }}
            autoComplete="off"
          />
          <div style={{ display: "flex", flex: "3 1 260px", gap: 8 }}>
            <input
              aria-label="model"
              list="promptdb-models"
              value={byo.model}
              onChange={(e) => setByo({ ...byo, model: e.target.value })}
              placeholder="model id, e.g. meta-llama/llama-3.3-70b-instruct"
              style={{ flex: 1, padding: "8px 10px", fontSize: 13 }}
              spellCheck={false}
            />
            <datalist id="promptdb-models">
              {models.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
            {canList && (
              <button onClick={loadModels} disabled={loading} style={{ padding: "8px 12px", fontSize: 12.5, whiteSpace: "nowrap" }}>
                {loading ? "loading…" : models.length ? `${models.length} models` : "load models"}
              </button>
            )}
          </div>
          {err && <p style={{ flexBasis: "100%", fontSize: 12.5, color: "var(--danger)", margin: "2px 0 0" }}>{err}</p>}
          <p className="prose" style={{ flexBasis: "100%", fontSize: 12, color: "var(--ink-muted)", margin: "4px 0 0", lineHeight: 1.5 }}>
            Any OpenAI-compatible model. Local models (Ollama, vLLM) run through the
            <strong style={{ color: "var(--ink)" }}> local connector</strong>, not the hosted demo. Your key stays in the browser.
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
