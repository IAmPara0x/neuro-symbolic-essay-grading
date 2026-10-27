"""Central configuration: model names, thresholds, grade scale, and fuzzy
membership-function parameters.

Everything a non-programmer might want to tune (thresholds, the grading policy
via rule sets, membership-function shapes) is collected here so the rest of the
code stays declarative.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
SAMPLE_DATASET = DATA_RAW / "sample_cs_answers.csv"
PROCESSED_DATASET = DATA_PROCESSED / "dataset.csv"

# --------------------------------------------------------------------------
# Models (all offline / open; downloaded once by the libraries themselves)
# --------------------------------------------------------------------------
SPACY_MODEL = "en_core_web_sm"
SBERT_MODEL = "all-MiniLM-L6-v2"          # bi-encoder, parent paper's family
SIMCSE_MODEL = "princeton-nlp/sup-simcse-bert-base-uncased"  # optional 2nd view
CROSS_ENCODER_MODEL = "cross-encoder/stsb-roberta-base"      # optional re-rank

# --------------------------------------------------------------------------
# Scoring scale
# --------------------------------------------------------------------------
SCORE_MIN = 0.0
SCORE_MAX = 100.0

# Human grades in the raw dataset use this scale; we rescale to 0-100.
HUMAN_SCALE_MIN = 0.0
HUMAN_SCALE_MAX = 5.0

# --------------------------------------------------------------------------
# Module thresholds (mirroring the parent paper where applicable)
# --------------------------------------------------------------------------
SIMILARITY_SENTENCE_THRESHOLD = 0.75      # paper's cosine threshold
NER_CARDINAL_THRESHOLD = 0.90             # paper's cardinal-value threshold
KEYWORD_TOP_N = 10                        # keywords extracted from reference

# --------------------------------------------------------------------------
# Fuzzy membership functions (universe 0-100 for every input and the output)
# Each entry is a (shape, params) pair. shape in {"trap", "tri"}.
# trap params = (a, b, c, d); tri params = (a, b, c).
# --------------------------------------------------------------------------
INPUT_MFS = {
    "Low":    ("trap", (0, 0, 20, 45)),
    "Medium": ("tri",  (30, 50, 70)),
    "High":   ("trap", (55, 80, 100, 100)),
}

OUTPUT_MFS = {
    "Poor":      ("trap", (0, 0, 15, 35)),
    "Average":   ("tri",  (25, 45, 60)),
    "Good":      ("tri",  (50, 65, 80)),
    "Excellent": ("trap", (70, 88, 100, 100)),
}

# Which grading policy to use: "strict" or "lenient". The two differ only in
# their rule base (see fuzzy_engine.RULE_SETS) -- no code changes required.
GRADING_POLICY = "strict"

# Mechanical metrics are reported on the scorecard and applied as a small,
# transparent penalty (never the main driver). Set to 0.0 to disable.
MECHANICS_PENALTY_WEIGHT = 0.10
