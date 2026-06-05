export type Column = { name: string; type: string; pk: boolean };
export type Table = { name: string; columns: Column[] };
export type Edge = { from: string; to: string };
export type Schema = { tables: Table[]; edges: Edge[] };

export type Usage = {
  daily_spend_usd: number;
  daily_cap_usd: number;
  ip_queries_used: number;
  ip_queries_limit: number;
  free_queries_left: number;
  demo_open: boolean;
};

export type QueryResult = {
  question: string;
  sql: string | null;
  columns: string[] | null;
  rows: (string | number | null)[][] | null;
  answer: string | null;
  error: string | null;
  cost_usd: number;
  latency_s?: number;
  usage?: Usage | null;
};

export type Provider = "anthropic" | "openai" | "ollama";

export type Byo = { provider: Provider; model: string; apiKey: string } | null;

// the agent's pipeline stages, in order
export const STAGES = [
  { node: "schema_retriever", label: "read schema" },
  { node: "sql_writer", label: "write SQL" },
  { node: "sql_validator", label: "guardrail" },
  { node: "sql_executor", label: "execute" },
  { node: "answer_synthesizer", label: "answer" },
] as const;

export type StageNode = (typeof STAGES)[number]["node"];
