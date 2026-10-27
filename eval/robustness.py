"""Robustness tests the parent paper never ran.

1. Paraphrase stability: lightly paraphrase student answers (synonym swaps) and
   measure how far the grade drifts. A stable grader drifts little.

2. Padding attack: append irrelevant filler to answers and check the grade does
   NOT rise. AES systems are historically gamed by verbosity; a good grader is
   resistant.

Usage:  python -m eval.robustness
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.preprocess import load_dataset    # noqa: E402
from src.grader import Grader               # noqa: E402

_SYNONYMS = {
    "linear": "sequential", "structure": "arrangement", "remove": "delete",
    "add": "insert", "element": "item", "follows": "obeys", "uses": "employs",
    "fast": "quick", "value": "amount", "store": "keep", "find": "locate",
}

_FILLER = (" In addition, it is worth noting that this is a very important topic "
           "that many students study carefully and at great length in their course "
           "work throughout the semester, as is often discussed in lectures.")


def paraphrase(text: str) -> str:
    def repl(m) -> str:
        w = str(m.group(0))
        return _SYNONYMS.get(w.lower(), w)
    return re.sub(r"[A-Za-z]+", repl, text)


def run(dataset_path: str | None = None) -> dict:
    df = load_dataset(Path(dataset_path) if dataset_path else None)
    grader = Grader()

    base, para, padded = [], [], []
    for row in df.itertuples():
        b = grader.grade(row.student_answer, row.reference_answer,
                         row.question).final_grade
        p = grader.grade(paraphrase(row.student_answer), row.reference_answer,
                         row.question).final_grade
        d = grader.grade(row.student_answer + _FILLER, row.reference_answer,
                         row.question).final_grade
        base.append(b); para.append(p); padded.append(d)

    base, para, padded = map(np.array, (base, para, padded))
    return {
        "n": len(df),
        "paraphrase_mean_abs_drift": round(float(np.mean(np.abs(para - base))), 2),
        "paraphrase_max_abs_drift": round(float(np.max(np.abs(para - base))), 2),
        "padding_mean_grade_change": round(float(np.mean(padded - base)), 2),
        "padding_pct_that_increased": round(
            100.0 * float(np.mean(padded > base + 1e-6)), 1),
    }


if __name__ == "__main__":
    res = run()
    print("=== Robustness ===")
    for k, v in res.items():
        print(f"  {k:<30} {v}")
    print("\nInterpretation: small paraphrase drift = stable; "
          "padding change near 0 (and few increases) = resistant to gaming.")
