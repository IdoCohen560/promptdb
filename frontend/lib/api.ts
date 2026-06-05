import type { Byo, QueryResult, Schema, Usage } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

/** A stable per-browser id so the demo quota is metered per user, not per shared IP. */
export function clientId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem("promptdb_cid");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("promptdb_cid", id);
  }
  return id;
}

export async function getSchema(): Promise<Schema> {
  const r = await fetch(`${API_BASE}/schema`);
  if (!r.ok) throw new Error(`schema ${r.status}`);
  return r.json();
}

/** A ready-to-use sample database (server-side); returns just its schema for the blueprint. */
export async function getSample(): Promise<Schema> {
  const r = await fetch(`${API_BASE}/sample`);
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `sample ${r.status}`);
  return body.schema;
}

/** Generate schema-grounded starter questions for a connected database. */
export async function suggestQuestions(schema: Schema, byo: Byo): Promise<string[]> {
  const f = modelFields(byo);
  const r = await fetch(`${API_BASE}/suggest`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Client-Id": clientId() },
    body: JSON.stringify({ schema, provider: f.provider, base_url: f.base_url, api_key: f.api_key }),
  });
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `suggest ${r.status}`);
  return body.questions || [];
}

/** Validate a user connection string and load its schema (SSRF-guarded server-side). */
export async function connectDatabase(databaseUrl: string): Promise<Schema> {
  const r = await fetch(`${API_BASE}/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ database_url: databaseUrl }),
  });
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `connect ${r.status}`);
  return body.schema;
}

export async function getUsage(): Promise<Usage> {
  const r = await fetch(`${API_BASE}/usage`, { headers: { "X-Client-Id": clientId() } });
  if (!r.ok) throw new Error(`usage ${r.status}`);
  return r.json();
}

/** Stream the demo path (server key) via SSE. Returns a cancel function. */
export function streamQuery(
  question: string,
  on: (ev: { node: string } & Partial<QueryResult>) => void,
  onError: (status: number, detail: string) => void,
): () => void {
  const url = `${API_BASE}/query/stream?q=${encodeURIComponent(question)}`;
  const es = new EventSource(url);
  es.onmessage = (e) => {
    const data = JSON.parse(e.data);
    on(data);
    if (data.node === "done") es.close();
  };
  es.onerror = async () => {
    es.close();
    // EventSource hides the HTTP status; re-probe with fetch to surface 402 cap messages.
    try {
      const r = await fetch(url);
      const body = await r.json().catch(() => ({}));
      onError(r.status, body.detail || "stream failed");
    } catch {
      onError(0, "connection failed");
    }
  };
  return () => es.close();
}

/** Map a Byo model choice to the request's provider/base_url pair (custom → base_url). */
function modelFields(byo: Byo) {
  if (!byo) return { provider: null, base_url: null, model: null, api_key: null };
  return {
    provider: byo.preset === "custom" ? null : byo.preset,
    base_url: byo.preset === "custom" ? byo.baseUrl : null,
    model: byo.model || null,
    api_key: byo.apiKey || null,
  };
}

/** List models from a provider's OpenAI-compatible /models route. */
export async function fetchModels(byo: Byo): Promise<string[]> {
  const f = modelFields(byo);
  const r = await fetch(`${API_BASE}/models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider: f.provider, base_url: f.base_url, api_key: f.api_key }),
  });
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `models ${r.status}`);
  return body.models;
}

/** POST path (used for BYO key and/or a connected database). Key + connection string travel in
 *  the body, never the URL. */
export async function postQuery(
  question: string,
  byo: Byo,
  databaseUrl: string | null,
  sample = false,
): Promise<QueryResult> {
  const r = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Client-Id": clientId() },
    body: JSON.stringify({ question, ...modelFields(byo), database_url: databaseUrl, sample }),
  });
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `query ${r.status}`);
  return body;
}
