"use client";

import { useMemo, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import type { Schema } from "@/lib/types";

gsap.registerPlugin(useGSAP);

const W = 158;
const ROW_H = 17;
const HEAD_H = 28;
const MAX_COLS_SHOWN = 5;
const GAP_X = 52;
const GAP_Y = 46;
const PAD = 28;

const nodeHeight = (shown: number) => HEAD_H + shown * ROW_H + 8;

/** The live database schema as an ER blueprint. Tables are nodes, foreign keys are ink-blue edges.
 *  Interactive: hover a table to light it and its relationships; the rest recedes. Edges draw in
 *  and nodes fade up on load (GSAP). Recedes (dimmed) once a query is running. */
export default function SchemaBlueprint({
  schema,
  dimmed,
  active,
  selected,
  onSelect,
}: {
  schema: Schema;
  dimmed: boolean;
  active: string[];
  selected?: string | null;
  onSelect?: (table: string) => void;
}) {
  const scope = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<string | null>(null);
  const n = schema.tables.length;
  const cols = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(n))));
  const activeSet = useMemo(() => new Set(active.map((a) => a.toLowerCase())), [active]);

  // adjacency from foreign keys
  const neighbors = useMemo(() => {
    const m = new Map<string, Set<string>>();
    const add = (a: string, b: string) => {
      if (!m.has(a)) m.set(a, new Set());
      m.get(a)!.add(b);
    };
    for (const e of schema.edges) { add(e.from, e.to); add(e.to, e.from); }
    return m;
  }, [schema.edges]);

  const lit = useMemo(() => {
    if (!hover) return null; // no hover → nothing dimmed
    return new Set<string>([hover, ...(neighbors.get(hover) ?? [])]);
  }, [hover, neighbors]);

  const layout = schema.tables.map((t, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const shown = Math.min(MAX_COLS_SHOWN, t.columns.length);
    return {
      table: t, shown,
      x: PAD + col * (W + GAP_X),
      y: PAD + row * (nodeHeight(MAX_COLS_SHOWN) + GAP_Y),
      h: nodeHeight(shown),
      cx: PAD + col * (W + GAP_X) + W / 2,
    };
  });
  const pos = new Map(layout.map((l) => [l.table.name, l]));
  const rows = Math.ceil(n / cols);
  const vw = PAD * 2 + cols * W + (cols - 1) * GAP_X;
  const vh = PAD * 2 + rows * nodeHeight(MAX_COLS_SHOWN) + (rows - 1) * GAP_Y;

  useGSAP(
    () => {
      gsap.from(".pdb-node", { opacity: 0, y: 10, duration: 0.5, ease: "expo.out", stagger: 0.04 });
      gsap.fromTo(".pdb-edge", { strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut", stagger: 0.05, delay: 0.2 });
    },
    { scope, dependencies: [schema] },
  );

  const nodeOpacity = (name: string) => (lit && !lit.has(name) ? 0.28 : 1);

  return (
    <svg
      ref={scope}
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
      <g fill="none">
        {schema.edges.map((e, i) => {
          const a = pos.get(e.from);
          const b = pos.get(e.to);
          if (!a || !b) return null;
          const ay = a.y + a.h / 2;
          const by = b.y + b.h / 2;
          const mx = (a.cx + b.cx) / 2;
          const hovHot = hover && (e.from === hover || e.to === hover);
          const sqlHot = activeSet.has(e.from.toLowerCase()) && activeSet.has(e.to.toLowerCase());
          const hot = hovHot || sqlHot;
          const dim = lit && !hovHot;
          return (
            <path
              key={i}
              className="pdb-edge"
              pathLength={1}
              strokeDasharray={1}
              d={`M ${a.cx} ${ay} C ${mx} ${ay}, ${mx} ${by}, ${b.cx} ${by}`}
              stroke={hot ? "var(--data-strong)" : "var(--line-soft)"}
              strokeWidth={hot ? 1.8 : 1}
              opacity={dim ? 0.12 : 0.7}
              style={{ transition: "opacity 0.2s, stroke 0.2s, stroke-width 0.2s" }}
            />
          );
        })}
      </g>

      {layout.map(({ table, x, y, h, shown }) => {
        const on = activeSet.has(table.name.toLowerCase()) || hover === table.name || selected === table.name;
        const lift = hover === table.name ? -3 : 0;
        return (
          <g
            key={table.name}
            className="pdb-node"
            onMouseEnter={() => setHover(table.name)}
            onMouseLeave={() => setHover(null)}
            onClick={() => onSelect?.(table.name)}
            style={{
              cursor: "pointer", opacity: nodeOpacity(table.name),
              transform: `translateY(${lift}px)`, transition: "opacity 0.2s, transform 0.2s var(--ease)",
            }}
          >
            <rect x={x} y={y} width={W} height={h} rx={3} fill="var(--paper-panel)"
                  stroke={selected === table.name ? "var(--data-strong)" : on ? "var(--line-strong)" : "var(--line)"}
                  strokeWidth={selected === table.name ? 2 : on ? 1.5 : 1}
                  style={{ transition: "stroke 0.2s, stroke-width 0.2s" }} />
            <rect x={x} y={y} width={W} height={HEAD_H} rx={3} fill={on ? "var(--line-strong)" : "var(--line)"} style={{ transition: "fill 0.2s" }} />
            <rect x={x} y={y + HEAD_H - 6} width={W} height={6} fill={on ? "var(--line-strong)" : "var(--line)"} style={{ transition: "fill 0.2s" }} />
            <text x={x + 10} y={y + 18} fill="var(--paper-panel)" fontFamily="var(--font-mono)" fontSize={12} fontWeight={600} letterSpacing="0.02em">
              {table.name}
            </text>
            {table.columns.slice(0, shown).map((c, j) => (
              <g key={c.name}>
                <text x={x + 10} y={y + HEAD_H + 13 + j * ROW_H} fill="var(--ink)" fontFamily="var(--font-mono)" fontSize={11} fontWeight={c.pk ? 600 : 400}>
                  {c.name}
                </text>
                {c.pk && (
                  <text x={x + W - 10} y={y + HEAD_H + 13 + j * ROW_H} fill="var(--data-strong)" fontFamily="var(--font-mono)" fontSize={9} fontWeight={600} textAnchor="end" letterSpacing="0.08em">
                    PK
                  </text>
                )}
              </g>
            ))}
            {table.columns.length > shown && (
              <text x={x + 10} y={y + HEAD_H + 13 + shown * ROW_H} fill="var(--ink-muted)" fontFamily="var(--font-mono)" fontSize={10}>
                +{table.columns.length - shown} more
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
