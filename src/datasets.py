"""Convert the Mohler (2011) UNT Computer Science Short Answer dataset into the
canonical CSV schema used by the rest of the project.

    question, reference_answer, student_answer, human_score (0-5), id

Run:  python -m src.datasets
Produces: data/processed/mohler.csv
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import config

MOHLER_ROOT = config.DATA_RAW / "mohler_extracted"
MOHLER_CSV = config.DATA_PROCESSED / "mohler.csv"


def _parse_keyed_file(path: Path) -> dict[str, str]:
    """Parse files like 'x.y <text>' into {qid: text}."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d+\.\d+)\s+(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _clean(text: str, qid: str) -> str:
    """Strip the leading 'x.y ' prefix, <STOP>/<br> markers, collapse space."""
    text = re.sub(rf"^{re.escape(qid)}\s+", "", text.strip())
    text = text.replace("<STOP>", " ").replace("<br>", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_mohler_csv(root: Path = MOHLER_ROOT, out: Path = MOHLER_CSV) -> pd.DataFrame:
    data = root / "data"
    if not data.exists():
        raise FileNotFoundError(
            f"Mohler data not found at {data}. Download and unzip "
            f"ShortAnswerGrading_v2.0 into {root}."
        )

    questions = _parse_keyed_file(data / "raw" / "questions")
    answers = _parse_keyed_file(data / "raw" / "answers")
    valid = [
        ln.strip() for ln in (data / "docs" / "files").read_text().splitlines()
        if ln.strip() and not ln.startswith("#")
    ]

    rows = []
    for qid in valid:
        sent_file = data / "sent" / qid
        score_file = data / "scores" / qid / "ave"
        if not (sent_file.exists() and score_file.exists()):
            continue
        students = sent_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        scores = score_file.read_text().splitlines()
        q_text = questions.get(qid, "")
        ref = answers.get(qid, "")
        for i, (stu, sc) in enumerate(zip(students, scores)):
            stu = _clean(stu, qid)
            sc = sc.strip()
            if not stu or not sc:
                continue
            try:
                grade = float(sc)
            except ValueError:
                continue
            # exams (assignments 11,12) were on 0..10; 'ave' is already
            # normalised to 0..5 per the README, but clamp defensively.
            grade = max(0.0, min(5.0, grade))
            rows.append({
                "id": f"{qid}.{i}",
                "question": q_text,
                "reference_answer": ref,
                "student_answer": stu,
                "human_score": grade,
            })

    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    df = build_mohler_csv()
    print(f"Built {MOHLER_CSV} with {len(df)} student answers "
          f"across {df['question'].nunique()} questions.")
    print(f"Grade range: {df['human_score'].min()}–{df['human_score'].max()}, "
          f"mean {df['human_score'].mean():.2f}")
    print(df[["id", "human_score"]].head())
