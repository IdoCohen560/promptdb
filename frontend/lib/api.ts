import type { Byo, QueryResult, Schema, Usage } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

export async function getSchema(): Promise<Schema> {
  const r = await fetch(`${API_BASE}/schema`);
  if (!r.ok) throw new Error(`schema ${r.status}`);
  return r.json();
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
  const r = await fetch(`${API_BASE}/usage`);
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

/** POST path (used for BYO key and/or a connected database). Key + connection string travel in
 *  the body, never the URL. */
export async function postQuery(
  question: string,
  byo: Byo,
  databaseUrl: string | null,
): Promise<QueryResult> {
  const r = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      provider: byo?.provider ?? null,
      model: byo?.model || null,
      api_key: byo?.apiKey || null,
      database_url: databaseUrl,
    }),
  });
  const body = await r.json();
  if (!r.ok) throw new Error(body.detail || `query ${r.status}`);
  return body;
}
