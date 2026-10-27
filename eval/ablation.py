"""Ablation study: how much does each module / the fuzzy layer contribute?

Compares, against human scores:
  * mean-baseline      -- predict the mean human score for everyone
  * keyword-only       -- use the keyword module score directly as the grade
  * similarity-only    -- use the semantic module score directly
  * ner-only           -- use the NER module score directly
  * mean-of-modules    -- simple average of the three (what a linear fuse does)
  * full (fuzzy)       -- the complete neuro-symbolic system

This mirrors the parent paper's per-module analysis while adding the key
question it could not ask: does the fuzzy rule base beat a plain average?

Usage:  python -m eval.ablation
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocess import load_dataset                         # noqa: E402
from src.grader import Grader                                    # noqa: E402
from src.modules import keyword, similarity, ner                 # noqa: E402
from src.preprocess import normalise                             # noqa: E402
from eval.run_eval import rmse, pearson, quadratic_weighted_kappa  # noqa: E402


def _metrics(pred, true):
    pred, true = np.asarray(pred), np.asarray(true)
    return {
        "rmse": round(rmse(pred, true), 2),
        "pearson": round(pearson(pred, true), 3),
        "qwk": round(quadratic_weighted_kappa(pred, true), 3),
    }


def run(dataset_path: str | None = None) -> dict:
    df = load_dataset(Path(dataset_path) if dataset_path else None)
    true = df["human_score"].to_numpy()
    grader = Grader()

    kw, sim, nr, full = [], [], [], []
    for row in df.itertuples():
        s, r = normalise(row.student_answer), normalise(row.reference_answer)
        kw.append(keyword.score(s, r).score)
        sim.append(similarity.score(s, r).score)
        nr.append(ner.score(s, r).score)
        full.append(grader.grade(row.student_answer, row.reference_answer,
                                 row.question).final_grade)

    kw, sim, nr, full = map(np.array, (kw, sim, nr, full))
    mean_modules = (kw + sim + nr) / 3.0
    mean_base = np.full_like(true, true.mean())

    systems = {
        "mean-baseline":  mean_base,
        "keyword-only":   kw,
        "similarity-only": sim,
        "ner-only":       nr,
        "mean-of-modules": mean_modules,
        "full (fuzzy)":   full,
    }
    return {name: _metrics(pred, true) for name, pred in systems.items()}


if __name__ == "__main__":
    results = run()
    print(f"{'system':<18}{'rmse':>8}{'pearson':>10}{'qwk':>8}")
    print("-" * 44)
    for name, m in results.items():
        print(f"{name:<18}{m['rmse']:>8}{m['pearson']:>10}{m['qwk']:>8}")
