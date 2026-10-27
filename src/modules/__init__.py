"""Scoring modules (symbolic + neural pathways).

Every module exposes a ``score(student, reference, question=None) -> ModuleResult``
function. The result carries a normalised 0-100 score plus an ``evidence`` dict
that the scorecard renders verbatim -- the evidence is what makes the grade
auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModuleResult:
    name: str
    score: float                              # normalised 0-100
    evidence: dict[str, Any] = field(default_factory=dict)
    backend: str = "unknown"                  # which implementation ran

    def __post_init__(self) -> None:
        self.score = max(0.0, min(100.0, float(self.score)))
