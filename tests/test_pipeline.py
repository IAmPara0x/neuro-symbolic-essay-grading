"""Unit tests. Run with:  python -m pytest -q   (or python tests/test_pipeline.py)

These are deterministic: they assert monotonic/relative behaviour rather than
exact scores, so they pass whether the heavy models or the fallbacks are active.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fuzzy_engine import FuzzyGrader, trimf, trapmf     # noqa: E402
from src.grader import grade_answer                          # noqa: E402
from src.modules import keyword, similarity, ner             # noqa: E402

import numpy as np

REF = ("A stack is a linear data structure that follows the Last In First Out "
       "principle using push and pop operations at the top.")
GOOD = ("A stack is a linear data structure following LIFO order using push and "
        "pop at the top.")
BAD = "A stack is a box where you put random things and the weather is nice today."


def test_membership_functions():
    x = np.linspace(0, 100, 101)
    assert trimf(x, 30, 50, 70).max() == 1.0
    assert trapmf(x, 55, 80, 100, 100)[-1] == 1.0
    assert trimf(x, 30, 50, 70)[0] == 0.0


def test_fuzzy_high_inputs_score_high():
    fg = FuzzyGrader("strict")
    hi = fg.grade({"keyword": 90, "similarity": 90, "ner": 90})
    lo = fg.grade({"keyword": 5, "similarity": 5, "ner": 5})
    assert hi.grade > lo.grade
    assert hi.grade > 65
    assert lo.grade < 45
    assert len(hi.fired_rules) >= 1


def test_fuzzy_trace_present():
    fg = FuzzyGrader("strict")
    res = fg.grade({"keyword": 85, "similarity": 20, "ner": 50})
    # the "terms without understanding" rule should fire
    assert any("understanding" in r.text for r in res.fired_rules)


def test_modules_run_and_bounded():
    for mod in (keyword, similarity, ner):
        r = mod.score(GOOD, REF)
        assert 0.0 <= r.score <= 100.0


def test_good_beats_bad_end_to_end():
    good = grade_answer(GOOD, REF, "What is a stack?").final_grade
    bad = grade_answer(BAD, REF, "What is a stack?").final_grade
    assert good > bad


def test_scorecard_serialises():
    card = grade_answer(GOOD, REF, "What is a stack?")
    d = card.to_dict()
    assert "final_grade" in d and "fired_rules" in d and "evidence" in d


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} tests passed")
    sys.exit(1 if failed else 0)
