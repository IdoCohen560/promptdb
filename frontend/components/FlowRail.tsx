import { STAGES, type StageNode } from "@/lib/types";

export type StageStatus = "pending" | "active" | "done" | "error";

const DOT: Record<StageStatus, string> = {
  pending: "var(--line-soft)",
  active: "var(--line-strong)",
  done: "var(--ok)",
  error: "var(--danger)",
};

/** The agent pipeline as a left-to-right schematic: english → SQL → rows → answer.
 *  Each stage lights up as it streams; a retry on error is shown honestly. */
export default function FlowRail({
  status,
  attempts,
}: {
  status: Record<StageNode, StageStatus>;
  attempts: number;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 0, rowGap: 10 }}>
      {STAGES.map((s, i) => {
        const st = status[s.node] ?? "pending";
        return (
          <div key={s.node} style={{ display: "flex", alignItems: "center" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 9,
                  height: 9,
                  borderRadius: "50%",
                  background: st === "pending" ? "transparent" : DOT[st],
                  border: `1.5px solid ${DOT[st]}`,
                  flexShrink: 0,
                  transition: "background 0.25s var(--ease), border-color 0.25s var(--ease)",
                }}
              />
              <span
                style={{
                  fontSize: 12,
                  letterSpacing: "0.04em",
                  color: st === "pending" ? "var(--ink-muted)" : "var(--ink)",
                  fontWeight: st === "active" ? 600 : 400,
                  whiteSpace: "nowrap",
                }}
              >
                {s.label}
                {s.node === "sql_writer" && attempts > 1 && (
                  <span style={{ color: "var(--danger)", marginLeft: 6 }}>×{attempts}</span>
                )}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <span
                aria-hidden
                style={{
                  width: 26,
                  height: 1,
                  margin: "0 12px",
                  background:
                    st === "done" ? "var(--line)" : "var(--line-soft)",
                  opacity: st === "done" ? 1 : 0.5,
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
