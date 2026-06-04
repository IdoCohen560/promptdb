"""P4: compare models on the gold set — execution accuracy, cost/query, latency.

Also validates that the eval harness discriminates between models.
Usage: python -m evals.compare_models
"""

import os
import time

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from evals.dataset import GOLD
from evals.evaluators import execution_match
from promptdb.agent.graph import SQLQuery, build_sql_prompt
from promptdb.db.connection import get_engine, get_schema_text, run_select
from promptdb.observability.cost import cost_usd

load_dotenv()

MODELS = os.environ.get(
    "PROMPTDB_COMPARE_MODELS", "claude-sonnet-4-6,claude-haiku-4-5-20251001"
).split(",")


def run_model(model: str, schema: str, engine) -> dict:
    llm = ChatAnthropic(model=model, temperature=0, max_tokens=1024).with_structured_output(
        SQLQuery, include_raw=True
    )
    correct = 0
    cost = 0.0
    latency = 0.0
    for item in GOLD:
        t0 = time.monotonic()
        try:
            out = llm.invoke(build_sql_prompt(schema, item["q"]))
            sql = out["parsed"].sql
            usage = getattr(out["raw"], "usage_metadata", None) or {}
        except Exception:  # noqa: BLE001
            latency += time.monotonic() - t0
            continue
        latency += time.monotonic() - t0
        cost += cost_usd(usage, model)
        try:
            pc, pr = run_select(engine, sql)
            gc, gr = run_select(engine, item["sql"])
            if execution_match(pc, pr, gc, gr):
                correct += 1
        except Exception:  # noqa: BLE001
            pass
    n = len(GOLD)
    return {"model": model, "acc": 100 * correct / n, "cost_q": cost / n, "lat_q": latency / n}


def main() -> None:
    engine = get_engine()
    schema = get_schema_text(engine)
    rows = [run_model(m.strip(), schema, engine) for m in MODELS]
    print(f"\n{'model':34s} {'accuracy':>9} {'cost/query':>11} {'latency/q':>10}")
    print("-" * 66)
    for r in rows:
        print(f"{r['model']:34s} {r['acc']:>7.1f}% {('$%.5f' % r['cost_q']):>11} {r['lat_q']:>9.2f}s")


if __name__ == "__main__":
    main()
