"""Mamdani fuzzy inference engine -- the project's core contribution.

This replaces the parent paper's opaque 4-layer DNN combiner with a transparent,
auditable rule base. It is a self-contained NumPy implementation (equivalent to
scikit-fuzzy) chosen deliberately so that the *firing strength of every rule* can
be reported -- that per-rule trace is the justification the DNN cannot produce.

Pipeline:  fuzzify  ->  evaluate IF-THEN rules (min conjunction / max disjunction)
           ->  clip + aggregate consequents (max)  ->  centroid defuzzification.

Inputs are the three parent-paper modules: keyword, similarity, ner (each 0-100).
Output is a grade 0-100 with linguistic sets Poor / Average / Good / Excellent.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import config

# --------------------------------------------------------------------------
# Membership functions
# --------------------------------------------------------------------------
def trimf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    y = np.zeros_like(x, dtype=float)
    if b > a:
        left = (x >= a) & (x <= b)
        y[left] = (x[left] - a) / (b - a)
    else:
        y[x == a] = 1.0
    if c > b:
        right = (x > b) & (x <= c)
        y[right] = (c - x[right]) / (c - b)
    else:
        y[x == b] = 1.0
    return np.clip(y, 0.0, 1.0)


def trapmf(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    y = np.zeros_like(x, dtype=float)
    if b > a:
        up = (x >= a) & (x < b)
        y[up] = (x[up] - a) / (b - a)
    y[(x >= b) & (x <= c)] = 1.0
    if d > c:
        down = (x > c) & (x <= d)
        y[down] = (d - x[down]) / (d - c)
    return np.clip(y, 0.0, 1.0)


def _build(mf_spec: dict[str, tuple[str, tuple]], x: np.ndarray) -> dict[str, np.ndarray]:
    out = {}
    for label, (shape, params) in mf_spec.items():
        out[label] = trapmf(x, *params) if shape == "trap" else trimf(x, *params)
    return out


def _membership(mf_spec: dict, universe: np.ndarray, crisp: float) -> dict[str, float]:
    """Degree of membership of a crisp value in each linguistic set."""
    return {
        label: float(np.interp(crisp, universe,
                               trapmf(universe, *p) if s == "trap"
                               else trimf(universe, *p)))
        for label, (s, p) in mf_spec.items()
    }


# --------------------------------------------------------------------------
# Rule representation
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Rule:
    """antecedents: list of (variable, linguistic_set); combined by `op`.
    consequent: output linguistic set.  text: human-readable description."""
    antecedents: tuple
    op: str                 # "and" (min) or "or" (max)
    consequent: str
    text: str
    weight: float = 1.0


# Two interchangeable grading policies -- the examiner edits these, not the code.
RULE_SETS: dict[str, list[Rule]] = {
    "strict": [
        Rule((("similarity", "High"), ("keyword", "High")), "and", "Excellent",
             "IF meaning is High AND keyword coverage is High THEN Excellent"),
        Rule((("similarity", "High"), ("ner", "High")), "and", "Good",
             "IF meaning is High AND entity overlap is High THEN Good"),
        Rule((("keyword", "High"), ("similarity", "Low")), "and", "Average",
             "IF keywords High BUT meaning Low THEN Average (terms without understanding)"),
        Rule((("similarity", "High"), ("keyword", "Low")), "and", "Good",
             "IF meaning High BUT keywords Low THEN Good (understands, imprecise wording)"),
        Rule((("similarity", "Medium"), ("keyword", "Medium")), "and", "Average",
             "IF meaning Medium AND keywords Medium THEN Average"),
        Rule((("similarity", "Low"), ("keyword", "Low")), "and", "Poor",
             "IF meaning Low AND keyword coverage Low THEN Poor"),
        Rule((("ner", "Low"), ("keyword", "Low")), "and", "Poor",
             "IF entity overlap Low AND keywords Low THEN Poor"),
        Rule((("similarity", "Medium"), ("keyword", "High")), "and", "Good",
             "IF meaning Medium AND keywords High THEN Good"),
    ],
    "lenient": [
        Rule((("similarity", "High"),), "or", "Excellent",
             "IF meaning is High THEN Excellent (ideas outweigh wording)"),
        Rule((("keyword", "High"), ("similarity", "Medium")), "and", "Good",
             "IF keywords High AND meaning Medium THEN Good"),
        Rule((("similarity", "Medium"),), "or", "Good",
             "IF meaning is Medium THEN Good"),
        Rule((("keyword", "Medium"), ("ner", "Medium")), "and", "Average",
             "IF keywords Medium AND entities Medium THEN Average"),
        Rule((("similarity", "Low"), ("keyword", "Low")), "and", "Poor",
             "IF meaning Low AND keywords Low THEN Poor"),
    ],
}


@dataclass
class FiredRule:
    text: str
    firing_strength: float
    consequent: str


@dataclass
class FuzzyResult:
    grade: float
    fired_rules: list[FiredRule]
    memberships: dict[str, dict[str, float]]   # per-input fuzzification
    aggregated: np.ndarray                      # aggregated output MF (for plotting)
    universe: np.ndarray


class FuzzyGrader:
    def __init__(self, policy: str | None = None, resolution: int = 501):
        self.policy = policy or config.GRADING_POLICY
        self.rules = RULE_SETS[self.policy]
        self.universe = np.linspace(config.SCORE_MIN, config.SCORE_MAX, resolution)
        self._out_mfs = _build(config.OUTPUT_MFS, self.universe)

    def grade(self, inputs: dict[str, float]) -> FuzzyResult:
        # 1. fuzzify each crisp input into its linguistic memberships
        memberships = {
            var: _membership(config.INPUT_MFS, self.universe, val)
            for var, val in inputs.items()
        }

        # 2. evaluate every rule -> firing strength
        aggregated = np.zeros_like(self.universe)
        fired: list[FiredRule] = []
        for rule in self.rules:
            degrees = []
            skip = False
            for var, term in rule.antecedents:
                if var not in memberships:          # input not provided
                    skip = True
                    break
                degrees.append(memberships[var][term])
            if skip or not degrees:
                continue
            strength = (min(degrees) if rule.op == "and" else max(degrees))
            strength *= rule.weight
            if strength <= 1e-6:
                continue
            # 3. clip the consequent set at the firing strength and aggregate
            clipped = np.minimum(strength, self._out_mfs[rule.consequent])
            aggregated = np.maximum(aggregated, clipped)
            fired.append(FiredRule(rule.text, round(float(strength), 3), rule.consequent))

        # 4. centroid defuzzification
        if aggregated.sum() > 0:
            grade = float((self.universe * aggregated).sum() / aggregated.sum())
        else:
            grade = 0.0

        fired.sort(key=lambda r: r.firing_strength, reverse=True)
        return FuzzyResult(grade, fired, memberships, aggregated, self.universe)
