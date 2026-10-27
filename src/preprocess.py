"""Text normalisation and dataset loading.

Normalisation mirrors the pre-processing block of the parent paper (Fig. 1):
lowercasing, contraction expansion, punctuation/whitespace stripping.

The dataset loader produces a single schema regardless of source:
    question, reference_answer, student_answer, human_score (0-100)

Supported sources:
  * the bundled sample CSV (default, zero downloads)
  * Mohler (2011) short-answer grading set, if placed in data/raw/
  * ASAP-SAS, if placed in data/raw/
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import config

_CONTRACTIONS = {
    "can't": "cannot", "won't": "will not", "n't": " not", "'re": " are",
    "'s": " is", "'d": " would", "'ll": " will", "'ve": " have", "'m": " am",
    "it's": "it is", "that's": "that is", "doesn't": "does not",
    "isn't": "is not", "aren't": "are not", "wasn't": "was not",
}


def expand_contractions(text: str) -> str:
    out = text
    for k, v in _CONTRACTIONS.items():
        out = re.sub(re.escape(k), v, out, flags=re.IGNORECASE)
    return out


def normalise(text: str, lower: bool = True) -> str:
    """Light, deterministic normalisation. Keeps the result human-readable."""
    if text is None:
        return ""
    t = str(text).strip()
    t = expand_contractions(t)
    if lower:
        t = t.lower()
    t = re.sub(r"\s+", " ", t)           # collapse whitespace
    t = re.sub(r"[ \t]+([.,;:!?])", r"\1", t)
    return t.strip()


def rescale_human(score: float) -> float:
    """Rescale a human grade from its native scale to 0-100."""
    lo, hi = config.HUMAN_SCALE_MIN, config.HUMAN_SCALE_MAX
    if hi == lo:
        return float(score)
    frac = (float(score) - lo) / (hi - lo)
    return max(config.SCORE_MIN, min(config.SCORE_MAX, frac * config.SCORE_MAX))


def load_dataset(path: Path | None = None) -> pd.DataFrame:
    """Load and normalise a dataset into the canonical schema.

    Returns columns: question, reference_answer, student_answer,
    human_score (0-100), human_score_raw (native scale).
    """
    path = Path(path) if path else config.SAMPLE_DATASET
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}. Use the bundled "
            f"{config.SAMPLE_DATASET.name} or drop Mohler/ASAP-SAS in data/raw/."
        )
    df = pd.read_csv(path)

    # Map common column aliases to the canonical names.
    aliases = {
        "model_answer": "reference_answer", "ref_answer": "reference_answer",
        "answer": "student_answer", "response": "student_answer",
        "score": "human_score", "grade": "human_score", "mark": "human_score",
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})

    required = {"question", "reference_answer", "student_answer", "human_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    df["human_score_raw"] = df["human_score"].astype(float)
    df["human_score"] = df["human_score_raw"].map(rescale_human)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    data = load_dataset()
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    data.to_csv(config.PROCESSED_DATASET, index=False)
    print(f"Loaded {len(data)} rows -> {config.PROCESSED_DATASET}")
    print(data[["question", "human_score_raw", "human_score"]].head())
