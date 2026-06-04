"""Run the execution-accuracy eval over the gold set.

Measures: execution accuracy, per-difficulty breakdown, latency, and token cost.
Usage: python evals/run_evals.py
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from evals.dataset import GOLD
from evals.evaluators import execution_match
from promptdb.agent.graph import SQLQuery, build_sql_prompt, get_llm
from promptdb.agent.guardrails import validate_sql
from promptdb.db.connection import get_engine, get_schema_text, run_select

load_dotenv()

# Per-Mtok pricing for the default model (Claude Sonnet 4.6: $3 in / $15 out).
PRICE_IN = float(os.environ.get("PROMPTDB_PRICE_IN", "3.0"))
PRICE_OUT = float(os.environ.get("PROMPTDB_PRICE_OUT", "15.0"))
RESULTS = Path(__file__).parent / "results" / "latest.json"


def generate_sql(schema: str, question: str) -> tuple[str, dict]:
    """Generate SQL and capture token usage from the raw model response."""
    llm = get_llm().with_structured_output(SQLQuery, include_raw=True)
    out = llm.invoke(build_sql_prompt(schema, question))
    usage = getattr(out["raw"], "usage_metadata", None) or {}
    return out["parsed"].sql, usage


def main() -> None:
    engine = get_engine()
    schema = get_schema_text(engine)
    rows_out = []
    total_cost = 0.0

    for item in GOLD:
        t0 = time.monotonic()
        try:
            pred_sql, usage = generate_sql(schema, item["q"])
        except Exception as exc:  # noqa: BLE001
            rows_out.append({**item, "correct": False, "reason": f"gen_error: {exc}"})
            continue
        latency = time.monotonic() - t0
        cost = (usage.get("input_tokens", 0) / 1e6) * PRICE_IN + (
            usage.get("output_tokens", 0) / 1e6
        ) * PRICE_OUT
        total_cost += cost

        verr = validate_sql(pred_sql)
        if verr:
            rows_out.append({**item, "correct": False, "reason": f"blocked: {verr}",
                             "pred": pred_sql, "latency": latency, "cost": cost})
            continue
        try:
            pred_cols, pred_rows = run_select(engine, pred_sql)
            gold_cols, gold_rows = run_select(engine, item["sql"])
            correct = execution_match(pred_cols, pred_rows, gold_cols, gold_rows)
            reason = "" if correct else "result_mismatch"
        except Exception as exc:  # noqa: BLE001
            correct, reason = False, f"exec_error: {exc}"
        rows_out.append({**item, "correct": correct, "reason": reason,
                         "pred": pred_sql, "latency": latency, "cost": cost})

    total = len(rows_out)
    correct = sum(1 for r in rows_out if r["correct"])
    acc = 100.0 * correct / total if total else 0.0

    by_diff: dict[str, list[bool]] = {}
    for r in rows_out:
        by_diff.setdefault(r["diff"], []).append(r["correct"])

    print(f"\n=== PromptDB eval — {get_llm().model} ===")
    print(f"Execution accuracy: {correct}/{total} = {acc:.1f}%")
    avg_lat = sum(r.get("latency", 0) for r in rows_out) / total if total else 0
    print(f"Avg latency: {avg_lat:.2f}s | Total cost: ${total_cost:.4f} "
          f"| Cost/query: ${total_cost / total:.5f}" if total else "")
    print("\nBy difficulty:")
    for diff, results in sorted(by_diff.items()):
        print(f"  {diff:14s} {sum(results)}/{len(results)}")
    fails = [r for r in rows_out if not r["correct"]]
    if fails:
        print("\nFailures:")
        for r in fails:
            print(f"  [{r['diff']}] {r['q']}  -> {r['reason']}")

    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(
        {"model": get_llm().model, "accuracy": acc, "correct": correct, "total": total,
         "cost_usd": total_cost, "avg_latency_s": avg_lat, "rows": rows_out}, indent=2, default=str))
    print(f"\nWrote {RESULTS}")


if __name__ == "__main__":
    main()
