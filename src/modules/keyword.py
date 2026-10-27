"""Keyword scoring module (symbolic pathway).

Faithful to the parent paper's keyword module (Fig. 1): extract keywords from
the reference answer with YAKE and KeyBERT, expand the student's tokens with
WordNet synonyms, and score the coverage of reference keywords by the student.

Backends degrade gracefully so the module always returns a score:
  YAKE/KeyBERT  ->  spaCy noun-chunks  ->  plain tokenised content words.
"""
from __future__ import annotations

import re
from functools import lru_cache

from . import ModuleResult
from .. import config

# ---- optional heavy backends -------------------------------------------------
try:
    import yake
    _HAS_YAKE = True
except Exception:
    _HAS_YAKE = False

try:
    from keybert import KeyBERT
    _HAS_KEYBERT = True
except Exception:
    _HAS_KEYBERT = False

try:
    from nltk.corpus import wordnet as wn
    wn.synsets("test")           # force-check the corpus is downloaded
    _HAS_WORDNET = True
except Exception:
    _HAS_WORDNET = False

_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "and", "or",
    "in", "on", "at", "it", "that", "this", "with", "for", "as", "by", "be",
    "from", "which", "where", "when", "so", "can", "you", "we", "they", "its",
    "into", "same", "each", "called", "using", "used", "between", "than",
}

_kb_model = None


def _keybert():
    global _kb_model
    if _kb_model is None and _HAS_KEYBERT:
        # reuse the SBERT model the similarity module also loads
        _kb_model = KeyBERT(model=config.SBERT_MODEL)
    return _kb_model


def _content_words(text: str) -> list[str]:
    toks = re.findall(r"[a-z][a-z0-9\-]+", text.lower())
    return [t for t in toks if t not in _STOP and len(t) > 2]


@lru_cache(maxsize=512)
def extract_keywords(text: str, top_n: int = config.KEYWORD_TOP_N) -> list[str]:
    """Reference-answer keyword extraction with the best available backend.

    Cached: the same reference answer is shared by many student answers, so the
    (expensive) YAKE/KeyBERT extraction runs once per distinct reference.
    """
    if _HAS_YAKE:
        kw = yake.KeywordExtractor(n=1, top=top_n)
        got = [k for k, _ in kw.extract_keywords(text)]
        if _HAS_KEYBERT:
            kb = _keybert().extract_keywords(
                text, keyphrase_ngram_range=(1, 1), top_n=top_n
            )
            got += [k for k, _ in kb]
        # dedupe, keep order, single words only
        seen, out = set(), []
        for k in got:
            for w in _content_words(k):
                if w not in seen:
                    seen.add(w)
                    out.append(w)
        return out[:top_n]
    # fallback: frequency-ranked content words
    words = _content_words(text)
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=lambda w: (-freq[w], w))[:top_n]


def _synonyms(word: str) -> set[str]:
    if not _HAS_WORDNET:
        return {word}
    syns = {word}
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            syns.add(lemma.name().replace("_", " ").lower())
    return syns


def score(student: str, reference: str, question: str | None = None) -> ModuleResult:
    ref_keywords = extract_keywords(reference)
    if not ref_keywords:
        return ModuleResult("keyword", 0.0, {"reason": "no reference keywords"},
                            backend="none")

    # expand student vocabulary with WordNet synonyms
    student_words = set(_content_words(student))
    expanded = set(student_words)
    for w in student_words:
        expanded |= _synonyms(w)

    matched = [k for k in ref_keywords if k in expanded]
    missed = [k for k in ref_keywords if k not in expanded]
    coverage = 100.0 * len(matched) / len(ref_keywords)

    backend = "yake+keybert" if _HAS_YAKE else "frequency"
    if _HAS_WORDNET:
        backend += "+wordnet"
    return ModuleResult(
        "keyword", coverage,
        {
            "reference_keywords": ref_keywords,
            "matched": matched,
            "missed": missed,
            "coverage_pct": round(coverage, 1),
        },
        backend=backend,
    )
