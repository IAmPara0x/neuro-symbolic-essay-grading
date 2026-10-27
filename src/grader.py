"""Top-level orchestration: run the modules, fuse with the fuzzy engine, and
assemble the explainable scorecard.

    grade_answer(student, reference, question) -> Scorecard(dict)

The scorecard is a plain dict so it serialises cleanly to JSON and renders in
Streamlit without extra glue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import config
from .preprocess import normalise
from .fuzzy_engine import FuzzyGrader, FuzzyResult
from .modules import keyword, similarity, ner, mechanics, ModuleResult


@dataclass
class Scorecard:
    final_grade: float
    letter: str
    module_scores: dict[str, float]
    modules: dict[str, ModuleResult]
    fuzzy: FuzzyResult
    policy: str
    mechanics_penalty: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "final_grade": round(self.final_grade, 1),
            "letter": self.letter,
            "policy": self.policy,
            "module_scores": {k: round(v, 1) for k, v in self.module_scores.items()},
            "mechanics_penalty": round(self.mechanics_penalty, 1),
            "fired_rules": [
                {"rule": r.text, "strength": r.firing_strength, "then": r.consequent}
                for r in self.fuzzy.fired_rules
            ],
            "evidence": {name: m.evidence for name, m in self.modules.items()},
            "backends": {name: m.backend for name, m in self.modules.items()},
        }


def _letter(grade: float) -> str:
    for cut, ltr in [(90, "A+"), (80, "A"), (70, "B"), (60, "C"),
                     (50, "D"), (0, "F")]:
        if grade >= cut:
            return ltr
    return "F"


class Grader:
    """Reusable grader; loads models once and grades many answers."""

    def __init__(self, policy: str | None = None):
        self.policy = policy or config.GRADING_POLICY
        self.fuzzy = FuzzyGrader(self.policy)

    def grade(self, student: str, reference: str,
              question: str | None = None) -> Scorecard:
        s = normalise(student)
        r = normalise(reference)

        kw = keyword.score(s, r, question)
        sim = similarity.score(s, r, question)
        nr = ner.score(s, r, question)
        mech = mechanics.score(s, r, question)

        modules = {"keyword": kw, "similarity": sim, "ner": nr, "mechanics": mech}
        module_scores = {k: m.score for k, m in modules.items()}

        # fuzzy inference over the three parent-paper modules
        fz = self.fuzzy.grade({
            "keyword": kw.score,
            "similarity": sim.score,
            "ner": nr.score,
        })

        # transparent mechanical penalty (advisory, never dominant)
        penalty = config.MECHANICS_PENALTY_WEIGHT * (100.0 - mech.score)
        final = max(config.SCORE_MIN, min(config.SCORE_MAX, fz.grade - penalty))

        return Scorecard(
            final_grade=final,
            letter=_letter(final),
            module_scores=module_scores,
            modules=modules,
            fuzzy=fz,
            policy=self.policy,
            mechanics_penalty=penalty,
            meta={"question": question},
        )


def grade_answer(student: str, reference: str, question: str | None = None,
                 policy: str | None = None) -> Scorecard:
    """Convenience one-shot entry point."""
    return Grader(policy).grade(student, reference, question)


if __name__ == "__main__":
    import json
    card = grade_answer(
        student="A stack is a linear structure using LIFO order with push and pop.",
        reference="A stack is a linear data structure that follows the Last In "
                  "First Out principle using push and pop operations at the top.",
        question="What is a stack?",
    )
    print(json.dumps(card.to_dict(), indent=2))
