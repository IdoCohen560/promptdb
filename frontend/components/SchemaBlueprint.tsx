import type { Schema } from "@/lib/types";

const W = 158;          // node width
const ROW_H = 17;       // per-column row height
const HEAD_H = 28;      // node title bar height
const MAX_COLS_SHOWN = 5;
const GAP_X = 52;
const GAP_Y = 46;
const PAD = 28;

function nodeHeight(shown: number) {
  return HEAD_H + shown * ROW_H + 8;
}

/** The live database schema as an ER blueprint — tables as nodes, foreign keys as ink-blue edges.
 *  It is the hero on first load and recedes (dimmed) once a query is running. */
export default function SchemaBlueprint({
  schema,
  dimmed,
  active,
}: {
  schema: Schema;
  dimmed: boolean;
  active: string[];
}) {
  const n = schema.tables.length;
  const cols = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(n))));
  const activeSet = new Set(active.map((a) => a.toLowerCase()));

  const layout = schema.tables.map((t, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const shown = Math.min(MAX_COLS_SHOWN, t.columns.length);
    return {
      table: t,
      shown,
      x: PAD + col * (W + GAP_X),
      y: PAD + row * (nodeHeight(MAX_COLS_SHOWN) + GAP_Y),
      h: nodeHeight(shown),
      cx: PAD + col * (W + GAP_X) + W / 2,
      cyTop: PAD + row * (nodeHeight(MAX_COLS_SHOWN) + GAP_Y),
    };
  });
  const pos = new Map(layout.map((l) => [l.table.name, l]));
  const rows = Math.ceil(n / cols);
  const vw = PAD * 2 + cols * W + (cols - 1) * GAP_X;
  const vh = PAD * 2 + rows * nodeHeight(MAX_COLS_SHOWN) + (rows - 1) * GAP_Y;

  return (
    <svg
      viewBox={`0 0 ${vw} ${vh}`}
      width="100%"
      role="img"
      aria-label="Database schema diagram"
      style={{
        maxHeight: dimmed ? 220 : 560,
        opacity: dimmed ? 0.32 : 1,
        filter: dimmed ? "saturate(0.6)" : "none",
        transition: "opacity 0.5s var(--ease), max-height 0.5s var(--ease), filter 0.5s var(--ease)",
      }}
    >
      {/* FK edges, drawn behind the nodes */}
      <g fill="none" stroke="var(--line-soft)" strokeWidth={1}>
        {schema.edges.map((e, i) => {
          const a = pos.get(e.from);
          const b = pos.get(e.to);
          if (!a || !b) return null;
          const ax = a.cx;
          const ay = a.y + a.h / 2;
          const bx = b.cx;
          const by = b.y + b.h / 2;
          const mx = (ax + bx) / 2;
          const hot = activeSet.has(e.from.toLowerCase()) && activeSet.has(e.to.toLowerCase());
          return (
            <path
              key={i}
              d={`M ${ax} ${ay} C ${mx} ${ay}, ${mx} ${by}, ${bx} ${by}`}
              stroke={hot ? "var(--data-strong)" : "var(--line-soft)"}
              strokeWidth={hot ? 1.6 : 1}
              opacity={0.7}
            />
          );
        })}
      </g>

      {/* table nodes */}
      {layout.map(({ table, x, y, h, shown }) => {
        const on = activeSet.has(table.name.toLowerCase());
        return (
          <g key={table.name}>
            <rect
              x={x}
              y={y}
              width={W}
              height={h}
              rx={3}
              fill="var(--paper-panel)"
              stroke={on ? "var(--line-strong)" : "var(--line)"}
              strokeWidth={on ? 1.5 : 1}
            />
            <rect x={x} y={y} width={W} height={HEAD_H} rx={3} fill={on ? "var(--line-strong)" : "var(--line)"} />
            <rect x={x} y={y + HEAD_H - 6} width={W} height={6} fill={on ? "var(--line-strong)" : "var(--line)"} />
            <text
              x={x + 10}
              y={y + 18}
              fill="var(--paper-panel)"
              fontFamily="var(--font-mono)"
              fontSize={12}
              fontWeight={600}
              letterSpacing="0.02em"
            >
              {table.name}
            </text>
            {table.columns.slice(0, shown).map((c, j) => (
              <g key={c.name}>
                <text
                  x={x + 10}
                  y={y + HEAD_H + 13 + j * ROW_H}
                  fill="var(--ink)"
                  fontFamily="var(--font-mono)"
                  fontSize={11}
                  fontWeight={c.pk ? 600 : 400}
                >
                  {c.name}
                </text>
                {c.pk && (
                  <text
                    x={x + W - 10}
                    y={y + HEAD_H + 13 + j * ROW_H}
                    fill="var(--data-strong)"
                    fontFamily="var(--font-mono)"
                    fontSize={9}
                    fontWeight={600}
                    textAnchor="end"
                    letterSpacing="0.08em"
                  >
                    PK
                  </text>
                )}
              </g>
            ))}
            {table.columns.length > shown && (
              <text
                x={x + 10}
                y={y + HEAD_H + 13 + shown * ROW_H}
                fill="var(--ink-muted)"
                fontFamily="var(--font-mono)"
                fontSize={10}
              >
                +{table.columns.length - shown} more
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
