type Cell = string | number | null;

function isNumeric(col: number, rows: Cell[][]) {
  let sawNumber = false;
  for (const r of rows) {
    const v = r[col];
    if (v === null || v === "") continue;
    if (typeof v === "number") { sawNumber = true; continue; }
    if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) { sawNumber = true; continue; }
    return false;
  }
  return sawNumber;
}

/** Result grid. Numeric columns carry an inline amber bar scaled to the column max:
 *  warm live data against the cool blueprint structure. */
export default function ResultTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: Cell[][];
}) {
  if (!columns.length) return null;
  const numericCols = columns.map((_, c) => isNumeric(c, rows));
  const maxAbs = columns.map((_, c) =>
    numericCols[c]
      ? Math.max(1, ...rows.map((r) => Math.abs(Number(r[c])) || 0))
      : 0,
  );

  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          borderCollapse: "collapse",
          width: "100%",
          fontFamily: "var(--font-mono)",
          fontSize: 13,
        }}
      >
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th
                key={c + i}
                style={{
                  textAlign: numericCols[i] ? "right" : "left",
                  padding: "7px 14px",
                  borderBottom: "1.5px solid var(--line)",
                  color: "var(--ink-muted)",
                  fontWeight: 600,
                  fontSize: 11,
                  letterSpacing: "0.06em",
                  textTransform: "uppercase",
                  whiteSpace: "nowrap",
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri}>
              {r.map((v, ci) => {
                const numeric = numericCols[ci];
                const frac = numeric ? (Math.abs(Number(v)) || 0) / maxAbs[ci] : 0;
                return (
                  <td
                    key={ci}
                    style={{
                      position: "relative",
                      textAlign: numeric ? "right" : "left",
                      padding: "6px 14px",
                      borderBottom: "1px solid var(--grid)",
                      color: v === null ? "var(--ink-muted)" : "var(--ink)",
                      fontVariantNumeric: "tabular-nums",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {numeric && (
                      <span
                        aria-hidden
                        style={{
                          position: "absolute",
                          right: 0,
                          top: 3,
                          bottom: 3,
                          width: `${Math.max(2, frac * 100)}%`,
                          background: "oklch(0.77 0.135 70 / 0.22)",
                          borderRight: "1.5px solid var(--data-strong)",
                          borderRadius: "2px 0 0 2px",
                        }}
                      />
                    )}
                    <span style={{ position: "relative" }}>{v === null ? "—" : String(v)}</span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
