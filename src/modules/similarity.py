"""Similarity scoring module (NEURAL pathway).

This is the project's neural component: a transformer sentence encoder (SBERT,
with SimCSE as an optional second view) measures semantic closeness between the
student answer and the reference answer -- the one judgement rules cannot make.

Mirrors the parent paper's similarity module: sentence tokenisation, per-sentence
cosine similarity, and the 0.75 threshold logic. Because everything runs locally,
there is no API and nothing to hallucinate; the number is a deterministic cosine.

Backends: sentence-transformers (SBERT)  ->  TF-IDF cosine (scikit-learn).
"""
from __future__ import annotations

import re

import numpy as np

from . import ModuleResult
from .. import config

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SBERT = True
except Exception:
    _HAS_SBERT = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _sk_cosine
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False

_sbert_model = None


def _sbert():
    global _sbert_model
    if _sbert_model is None and _HAS_SBERT:
        _sbert_model = SentenceTransformer(config.SBERT_MODEL)
    return _sbert_model


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


# Cache normalised embeddings by text. References are shared by many student
# answers, so this avoids re-encoding them on every grade() call.
_emb_cache: dict[str, np.ndarray] = {}


def _encode(text: str) -> np.ndarray:
    hit = _emb_cache.get(text)
    if hit is None:
        hit = _sbert().encode(text, normalize_embeddings=True)
        hit = np.asarray(hit, dtype=float)
        _emb_cache[text] = hit
    return hit


def _encode_sentences(text: str) -> np.ndarray:
    """Return a (n_sentences, dim) matrix of normalised sentence embeddings."""
    key = "\x00SENT\x00" + text
    hit = _emb_cache.get(key)
    if hit is None:
        sents = _sentences(text)
        hit = (np.asarray(_sbert().encode(sents, normalize_embeddings=True),
                          dtype=float)
               if sents else np.empty((0, 0)))
        _emb_cache[key] = hit
    return hit


def _sbert_score(student: str, reference: str) -> tuple[float, dict]:
    # document-level cosine (both embeddings normalised -> dot product = cosine)
    doc_cos = float(np.dot(_encode(student), _encode(reference)))

    # per-sentence best-match coverage against the reference (paper's approach)
    r_sents = _sentences(reference)
    coverage = doc_cos
    matched = 0
    se = _encode_sentences(student)
    re_ = _encode_sentences(reference)
    if se.size and re_.size:
        sim = re_ @ se.T                                  # ref x student
        best = sim.max(axis=1)                            # best student per ref sent
        matched = int((best >= config.SIMILARITY_SENTENCE_THRESHOLD).sum())
        coverage = float(best.mean())

    # blend document cosine and reference-sentence coverage
    cos = 0.5 * doc_cos + 0.5 * coverage
    score = float(np.clip(cos, 0.0, 1.0) * 100.0)
    evidence = {
        "document_cosine": round(doc_cos, 3),
        "mean_ref_sentence_match": round(coverage, 3),
        "ref_sentences_covered": f"{matched}/{len(r_sents)}" if r_sents else "n/a",
        "threshold": config.SIMILARITY_SENTENCE_THRESHOLD,
    }
    return score, evidence


def _tfidf_score(student: str, reference: str) -> tuple[float, dict]:
    vec = TfidfVectorizer(stop_words="english")
    try:
        m = vec.fit_transform([student, reference])
        cos = float(_sk_cosine(m[0], m[1])[0, 0])
    except ValueError:
        cos = 0.0
    return cos * 100.0, {"tfidf_cosine": round(cos, 3)}


def score(student: str, reference: str, question: str | None = None) -> ModuleResult:
    if _HAS_SBERT:
        s, ev = _sbert_score(student, reference)
        return ModuleResult("similarity", s, ev, backend="sbert")
    if _HAS_SKLEARN:
        s, ev = _tfidf_score(student, reference)
        ev["note"] = "SBERT unavailable; using TF-IDF cosine fallback"
        return ModuleResult("similarity", s, ev, backend="tfidf")
    # last resort: token Jaccard
    a, b = set(student.lower().split()), set(reference.lower().split())
    jac = 100.0 * len(a & b) / len(a | b) if (a | b) else 0.0
    return ModuleResult("similarity", jac, {"jaccard": round(jac, 1)}, backend="jaccard")
