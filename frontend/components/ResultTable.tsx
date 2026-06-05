"use client";

import { useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";

gsap.registerPlugin(useGSAP);

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

/** Result grid. Numeric columns carry an inline amber bar scaled to the column max (warm live
 *  data against the cool blueprint). Bars grow in with GSAP; hovering a value reveals its share. */
export default function ResultTable({ columns, rows }: { columns: string[]; rows: Cell[][] }) {
  const scope = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<{ r: number; c: number } | null>(null);

  const numericCols = columns.map((_, c) => isNumeric(c, rows));
  const maxAbs = columns.map((_, c) =>
    numericCols[c] ? Math.max(1, ...rows.map((r) => Math.abs(Number(r[c])) || 0)) : 0,
  );

  useGSAP(
    () => {
      gsap.from(".pdb-bar", {
        scaleX: 0, transformOrigin: "left center", duration: 0.75, ease: "expo.out", stagger: 0.025,
      });
      gsap.from(".pdb-row", { opacity: 0, y: 4, duration: 0.4, ease: "power3.out", stagger: 0.02 });
    },
    { scope, dependencies: [rows, columns] },
  );

  if (!columns.length) return null;

  return (
    <div ref={scope} style={{ overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%", fontFamily: "var(--font-mono)", fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th
                key={c + i}
                style={{
                  textAlign: numericCols[i] ? "right" : "left", padding: "7px 14px",
                  borderBottom: "1.5px solid var(--line)", color: "var(--ink-muted)", fontWeight: 600,
                  fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", whiteSpace: "nowrap",
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={ri} className="pdb-row" style={{ transition: "background 0.15s" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "oklch(0.96 0.02 250)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
              {r.map((v, ci) => {
                const numeric = numericCols[ci];
                const frac = numeric ? (Math.abs(Number(v)) || 0) / maxAbs[ci] : 0;
                const isHot = hover?.r === ri && hover?.c === ci;
                return (
                  <td
                    key={ci}
                    onMouseEnter={() => numeric && setHover({ r: ri, c: ci })}
                    onMouseLeave={() => setHover(null)}
                    style={{
                      position: "relative", textAlign: numeric ? "right" : "left", padding: "6px 14px",
                      borderBottom: "1px solid var(--grid)", color: v === null ? "var(--ink-muted)" : "var(--ink)",
                      fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap",
                      cursor: numeric ? "default" : "auto",
                    }}
                  >
                    {numeric && (
                      <span
                        className="pdb-bar"
                        aria-hidden
                        style={{
                          position: "absolute", right: 0, top: 3, bottom: 3, width: `${Math.max(2, frac * 100)}%`,
                          background: isHot ? "oklch(0.77 0.135 70 / 0.42)" : "oklch(0.77 0.135 70 / 0.22)",
                          borderRight: "1.5px solid var(--data-strong)", borderRadius: "2px 0 0 2px",
                          transition: "background 0.15s",
                        }}
                      />
                    )}
                    {numeric && isHot && (
                      <span
                        style={{
                          position: "absolute", right: 6, top: -18, fontSize: 10.5, fontWeight: 600,
                          color: "oklch(0.45 0.13 64)", background: "var(--paper-panel)",
                          border: "1px solid var(--data-strong)", borderRadius: 3, padding: "1px 5px", zIndex: 2,
                          whiteSpace: "nowrap",
                        }}
                      >
                        {Math.round(frac * 100)}% of max
                      </span>
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
