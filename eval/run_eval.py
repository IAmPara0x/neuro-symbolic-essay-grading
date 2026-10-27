"""Evaluate the full system against human scores.

Metrics (the parent paper reported RMSE only; we add agreement metrics):
  * RMSE            -- comparable in spirit to the parent paper
  * Pearson r       -- linear correlation with human marks
  * Quadratic Weighted Kappa (QWK) -- the standard AES agreement metric

Usage:  python -m eval.run_eval [path/to/dataset.csv]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocess import load_dataset          # noqa: E402
from src.grader import Grader                      # noqa: E402


def rmse(pred: np.ndarray, true: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - true) ** 2)))


def pearson(pred: np.ndarray, true: np.ndarray) -> float:
    if pred.std() == 0 or true.std() == 0:
        return 0.0
    return float(np.corrcoef(pred, true)[0, 1])


def quadratic_weighted_kappa(pred: np.ndarray, true: np.ndarray,
                             n_bins: int = 6) -> float:
    """QWK on scores binned onto a common integer scale (0..n_bins-1)."""
    def binify(x):
        b = np.floor(x / (100.0 / n_bins)).astype(int)
        return np.clip(b, 0, n_bins - 1)

    p, t = binify(pred), binify(true)
    O = np.zeros((n_bins, n_bins))
    for a, b in zip(t, p):
        O[a, b] += 1
    w = np.zeros((n_bins, n_bins))
    for i in range(n_bins):
        for j in range(n_bins):
            w[i, j] = (i - j) ** 2 / (n_bins - 1) ** 2
    act_hist = O.sum(axis=1)
    pred_hist = O.sum(axis=0)
    E = np.outer(act_hist, pred_hist) / max(O.sum(), 1)
    num = (w * O).sum()
    den = (w * E).sum()
    return float(1 - num / den) if den > 0 else 0.0


def evaluate(dataset_path: str | None = None, policy: str = "strict"):
    df = load_dataset(Path(dataset_path) if dataset_path else None)
    grader = Grader(policy)
    preds = np.array([
        grader.grade(row.student_answer, row.reference_answer, row.question).final_grade
        for row in df.itertuples()
    ])
    true = df["human_score"].to_numpy()
    results = {
        "n": len(df),
        "policy": policy,
        "rmse_0_100": round(rmse(preds, true), 2),
        "rmse_normalised": round(rmse(preds / 100, true / 100), 4),
        "pearson_r": round(pearson(preds, true), 3),
        "qwk": round(quadratic_weighted_kappa(preds, true), 3),
    }
    return results, preds, true


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    res, preds, true = evaluate(path)
    print("=== Full system vs human scores ===")
    for k, v in res.items():
        print(f"  {k:<18} {v}")
