"""Execution-accuracy metric with column-subset tolerance.

A prediction is correct if some projection of its columns reproduces the gold result
set (row order ignored). This forgives extra or reordered columns — a well-known
execution-accuracy artifact — without accepting wrong values.
"""

from itertools import permutations


def _normalize(rows: list[list]) -> list[tuple]:
    """Canonicalize rows: round float noise, sort so row order doesn't matter."""
    out = [tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows]
    return sorted(out, key=lambda t: tuple(str(c) for c in t))


def execution_match_strict(pred_rows: list[list], gold_rows: list[list]) -> bool:
    """Exact result-set match (order-insensitive) — comparable to official Spider exec accuracy."""
    return _normalize(pred_rows) == _normalize(gold_rows)


def execution_match(
    pred_cols: list[str], pred_rows: list[list],
    gold_cols: list[str], gold_rows: list[list],
) -> bool:
    """True if any column-projection of the prediction reproduces the gold result set."""
    gold = _normalize(gold_rows)
    n_gold, n_pred = len(gold_cols), len(pred_cols)
    if n_gold > n_pred:
        return _normalize(pred_rows) == gold
    for idx in permutations(range(n_pred), n_gold):
        if _normalize([tuple(r[i] for i in idx) for r in pred_rows]) == gold:
            return True
    return False
