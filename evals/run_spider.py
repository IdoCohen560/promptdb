"""P3b: execution-accuracy on a Spider dev sample (real public benchmark).

Questions from `xlangai/spider`; databases from `premai-io/spider`. Uses STRICT execution
match (full result set, order-insensitive) to be comparable to official Spider numbers.
Usage: python -m evals.run_spider [N]   (or env PROMPTDB_SPIDER_N, default 100)
"""

import json
import os
import sys
import time
from pathlib import Path

from datasets import load_dataset
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from langchain_anthropic import ChatAnthropic
from sqlalchemy import create_engine

from evals.evaluators import execution_match_strict
from promptdb.agent.graph import SQLQuery, build_sql_prompt
from promptdb.db.connection import get_schema_text, run_select
from promptdb.observability.cost import cost_usd

load_dotenv()

N = int(os.environ.get("PROMPTDB_SPIDER_N", sys.argv[1] if len(sys.argv) > 1 else "100"))
MODEL = os.environ.get("PROMPTDB_MODEL", "claude-sonnet-4-6")
DB_DIR = Path("spider_db")
EVAL_ROWS = 10_000  # high cap so the row limit never causes a false mismatch


def engine_for(db_id: str):
    path = hf_hub_download(
        repo_id="premai-io/spider",
        filename=f"database/{db_id}/{db_id}.sqlite",
        repo_type="dataset",
        local_dir=str(DB_DIR),
    )
    return create_engine(f"sqlite:///file:{path}?mode=ro&uri=true")


def main() -> None:
    ds = load_dataset("xlangai/spider", split="validation")
    items = ds.select(range(min(N, len(ds))))
    llm = ChatAnthropic(model=MODEL, temperature=0, max_tokens=1024).with_structured_output(
        SQLQuery, include_raw=True
    )
    engines: dict = {}
    correct = cost = latency = 0.0
    errors = 0
    n = len(items)

    for ex in items:
        db_id, question, gold = ex["db_id"], ex["question"], ex["query"]
        try:
            if db_id not in engines:
                engines[db_id] = engine_for(db_id)
            engine = engines[db_id]
            schema = get_schema_text(engine)
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        t0 = time.monotonic()
        try:
            out = llm.invoke(build_sql_prompt(schema, question))
            sql = out["parsed"].sql
            usage = getattr(out["raw"], "usage_metadata", None) or {}
        except Exception:  # noqa: BLE001
            latency += time.monotonic() - t0
            errors += 1
            continue
        latency += time.monotonic() - t0
        cost += cost_usd(usage, MODEL)
        try:
            _, pred_rows = run_select(engine, sql, max_rows=EVAL_ROWS)
            _, gold_rows = run_select(engine, gold, max_rows=EVAL_ROWS)
            if execution_match_strict(pred_rows, gold_rows):
                correct += 1
        except Exception:  # noqa: BLE001 — bad pred SQL counts as wrong
            pass

    acc = 100 * correct / n if n else 0
    print(f"\n=== Spider dev sample ({n} questions) — {MODEL} ===")
    print(f"Execution accuracy (strict): {int(correct)}/{n} = {acc:.1f}%")
    if n:
        print(f"Avg latency: {latency / n:.2f}s | Total cost: ${cost:.3f} "
              f"| Cost/query: ${cost / n:.5f}")
    print(f"Skipped (db/gen errors): {errors}")

    Path("evals/results").mkdir(exist_ok=True)
    Path("evals/results/spider.json").write_text(json.dumps(
        {"benchmark": "spider-dev-sample", "n": n, "model": MODEL, "accuracy": acc,
         "correct": int(correct), "cost_usd": cost,
         "avg_latency_s": latency / n if n else 0}, indent=2))


if __name__ == "__main__":
    main()
