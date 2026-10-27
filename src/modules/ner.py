"""NER scoring module (symbolic pathway).

Faithful to the parent paper's NER module (Fig. 3): extract named entities and
cardinal/numeric values from both answers and score the overlap as
|common| / |union| (Jaccard over entity sets).

The parent paper used spaCy / NLTK / CamemBERT-NER. CamemBERT is French-trained,
so for English CS answers spaCy is the primary backend (see PROJECT_PLAN risk
table); noun-chunk + number extraction is the dependency-free fallback.
"""
from __future__ import annotations

import re
from functools import lru_cache

from . import ModuleResult
from .. import config

_NLP = None

try:
    import spacy
    _HAS_SPACY = True
except Exception:
    _HAS_SPACY = False

_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
# domain terms that behave like entities in CS answers but spaCy may miss
_TERM_RE = re.compile(r"\bO\([^)]*\)", re.IGNORECASE)   # big-O expressions


def _nlp():
    global _NLP
    if _NLP is None and _HAS_SPACY:
        try:
            _NLP = spacy.load(config.SPACY_MODEL)
        except Exception:
            _NLP = spacy.blank("en")
    return _NLP


@lru_cache(maxsize=4096)
def _entities(text: str) -> set[str]:
    ents: set[str] = set()
    if _HAS_SPACY and _nlp() is not None and _nlp().has_pipe("ner"):
        for e in _nlp()(text).ents:
            ents.add(e.text.lower().strip())
    # always add numbers and big-O expressions as "cardinal"-style entities
    ents |= {m.group().lower() for m in _NUMBER_RE.finditer(text)}
    ents |= {m.group().lower().replace(" ", "") for m in _TERM_RE.finditer(text)}
    # fallback: capitalised tokens as proper-noun proxies
    if not _HAS_SPACY:
        ents |= {w.lower() for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)}
    return {e for e in ents if e}


def score(student: str, reference: str, question: str | None = None) -> ModuleResult:
    ref_ents = _entities(reference)
    stu_ents = _entities(student)

    if not ref_ents:
        # no entities to check against -> neutral, don't penalise
        return ModuleResult(
            "ner", 100.0,
            {"reference_entities": [], "note": "no entities in reference; neutral"},
            backend="spacy" if _HAS_SPACY else "regex",
        )

    common = ref_ents & stu_ents
    union = ref_ents | stu_ents
    overlap = 100.0 * len(common) / len(union)

    return ModuleResult(
        "ner", overlap,
        {
            "reference_entities": sorted(ref_ents),
            "student_entities": sorted(stu_ents),
            "common": sorted(common),
            "missing": sorted(ref_ents - stu_ents),
            "overlap_pct": round(overlap, 1),
        },
        backend="spacy" if _HAS_SPACY else "regex",
    )
