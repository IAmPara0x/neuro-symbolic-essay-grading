"""Mechanical-metrics module (symbolic pathway, advisory).

Adds the one axis the parent paper lacked: surface mechanical correctness
(length adequacy, grammar errors, syntactic depth). These feed the scorecard and
apply a small, transparent penalty via config.MECHANICS_PENALTY_WEIGHT -- they
never dominate the grade.

Backends:
  grammar  : language-tool-python (needs Java)  ->  heuristic repeated-word check
  depth    : spaCy dependency parse             ->  mean words-per-sentence proxy
"""
from __future__ import annotations

import re
from functools import lru_cache

from . import ModuleResult
from .. import config

_LT = None
_NLP = None

try:
    import language_tool_python
    _HAS_LT = True
except Exception:
    _HAS_LT = False

try:
    import spacy
    _HAS_SPACY = True
except Exception:
    _HAS_SPACY = False


def _lt():
    global _LT
    if _LT is None and _HAS_LT:
        try:
            _LT = language_tool_python.LanguageTool("en-US")
        except Exception:
            return None
    return _LT


def _nlp():
    global _NLP
    if _NLP is None and _HAS_SPACY:
        try:
            _NLP = spacy.load(config.SPACY_MODEL)
        except Exception:
            _NLP = spacy.blank("en")
    return _NLP


@lru_cache(maxsize=4096)
def _grammar_errors(text: str) -> int:
    tool = _lt() if _HAS_LT else None
    if tool is not None:
        try:
            return len(tool.check(text))
        except Exception:
            pass
    # heuristic fallback: immediate word repetitions + missing capitalisation
    errors = len(re.findall(r"\b(\w+)\s+\1\b", text.lower()))
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    errors += sum(1 for s in sents if s[:1].islower())
    return errors


@lru_cache(maxsize=4096)
def _mean_depth(text: str) -> float:
    nlp = _nlp()
    if nlp is not None and nlp.has_pipe("parser"):
        doc = nlp(text)
        depths = []
        for sent in doc.sents:
            for tok in sent:
                d, cur = 0, tok
                while cur.head != cur:
                    d += 1
                    cur = cur.head
                depths.append(d)
        return sum(depths) / len(depths) if depths else 0.0
    # proxy: average words per sentence / 5
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    words = len(text.split())
    return (words / len(sents) / 5.0) if sents else 0.0


def score(student: str, reference: str, question: str | None = None) -> ModuleResult:
    words = len(student.split())
    ref_words = max(1, len(reference.split()))
    length_ratio = words / ref_words
    # length adequacy: full marks around the reference length, less if far off
    length_adequacy = max(0.0, 1.0 - abs(1.0 - min(length_ratio, 2.0)))

    errors = _grammar_errors(student)
    error_rate = errors / max(1, words)
    cleanliness = max(0.0, 1.0 - 4.0 * error_rate)

    depth = _mean_depth(student)
    depth_adequacy = min(1.0, depth / 3.0)     # ~3 is a healthy mean depth

    mech = 100.0 * (0.4 * length_adequacy + 0.4 * cleanliness + 0.2 * depth_adequacy)
    backend = ("languagetool" if _HAS_LT else "heuristic") + \
              ("+spacy" if _HAS_SPACY else "")
    return ModuleResult(
        "mechanics", mech,
        {
            "word_count": words,
            "reference_word_count": ref_words,
            "length_ratio": round(length_ratio, 2),
            "grammar_errors": errors,
            "mean_dependency_depth": round(depth, 2),
        },
        backend=backend,
    )
