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

# Output sets (grade universe). Reshaped so the upper sets sit higher and a
# "VeryGood" set is added, reducing the range compression of centroid
# defuzzification (Lever 4). Calibration (src/calibration.py) handles the rest.
OUTPUT_MFS = {
    "Poor":      ("trap", (0, 0, 12, 28)),
    "Average":   ("tri",  (20, 38, 55)),
    "Good":      ("tri",  (48, 62, 76)),
    "VeryGood":  ("tri",  (70, 82, 92)),
    "Excellent": ("trap", (85, 94, 100, 100)),
}

# Inputs the fuzzy engine actually decides on. NER is still computed and shown
# on the scorecard as evidence, but is excluded from the decision because it is
# empirically near-random on the Mohler corpus (Pearson 0.07) -- a benefit of
# symbolic control: a bad sensor can be dropped without retraining (Lever 1).
FUZZY_INPUTS = ["keyword", "similarity"]

# Which grading policy to use: "strict" or "lenient". The two differ only in
# their rule base (see fuzzy_engine.RULE_SETS) -- no code changes required.
GRADING_POLICY = "lenient"

# Mechanical metrics are reported on the scorecard and applied as a small,
# transparent penalty (never the main driver). Set to 0.0 to disable.
MECHANICS_PENALTY_WEIGHT = 0.10

# --------------------------------------------------------------------------
# Neural similarity: prefer a cross-encoder for the (student, reference) pair
# score when available (far better pairwise STS than a bi-encoder), falling
# back to the bi-encoder and then TF-IDF (Lever 2).
# --------------------------------------------------------------------------
USE_CROSS_ENCODER = True

# --------------------------------------------------------------------------
# Calibration: an optional, transparent final rescaling of the fuzzy grade to
# the human mark scale, fit once on a dataset (Lever 4). Applied by the grader
# if the params file exists.
# --------------------------------------------------------------------------
CALIBRATION_PATH = ROOT / "results" / "calibration_params.json"
APPLY_CALIBRATION = True
