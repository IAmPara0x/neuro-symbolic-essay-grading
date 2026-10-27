"""Scorecard rendering: a text transcript and matplotlib membership-function
plots. The plots visualise fuzzification of each input and the aggregated output
membership with the defuzzified mark -- i.e. the decision made visible.
"""
from __future__ import annotations

import numpy as np

from . import config
from .fuzzy_engine import trimf, trapmf
from .grader import Scorecard


def format_text(card: Scorecard) -> str:
    """A compact, printable justification -- the explanation *is* the computation."""
    lines = []
    lines.append(f"FINAL GRADE: {card.final_grade:.1f}/100  ({card.letter})   "
                 f"[policy: {card.policy}]")
    lines.append("-" * 64)
    lines.append("Module scores (0-100):")
    for name, score in card.module_scores.items():
        pathway = "neural" if name == "similarity" else "symbolic"
        lines.append(f"  {name:<12} {score:6.1f}   ({pathway}, "
                     f"{card.modules[name].backend})")
    if card.mechanics_penalty:
        lines.append(f"  mechanical penalty applied: -{card.mechanics_penalty:.1f}")
    lines.append("")
    lines.append("Fuzzy rules that fired (the justification):")
    if not card.fuzzy.fired_rules:
        lines.append("  (none fired)")
    for r in card.fuzzy.fired_rules:
        lines.append(f"  [{r.firing_strength:.2f}] {r.text}")
    lines.append("")
    lines.append("Key evidence:")
    kw = card.modules["keyword"].evidence
    if "matched" in kw:
        lines.append(f"  keywords matched : {', '.join(kw['matched']) or '-'}")
        lines.append(f"  keywords missed  : {', '.join(kw['missed']) or '-'}")
    sim = card.modules["similarity"].evidence
    if "document_cosine" in sim:
        lines.append(f"  semantic cosine  : {sim['document_cosine']}")
    nr = card.modules["ner"].evidence
    if "common" in nr:
        lines.append(f"  entities matched : {', '.join(nr['common']) or '-'}")
    return "\n".join(lines)


def plot_scorecard(card: Scorecard):
    """Return a matplotlib Figure: input fuzzifications + aggregated output."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    inputs = ["keyword", "similarity", "ner"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    axes = axes.ravel()
    x = np.linspace(config.SCORE_MIN, config.SCORE_MAX, 501)

    # input membership plots with the crisp value marked
    for ax, var in zip(axes[:3], inputs):
        for label, (shape, p) in config.INPUT_MFS.items():
            y = trapmf(x, *p) if shape == "trap" else trimf(x, *p)
            ax.plot(x, y, label=label)
        val = card.module_scores[var]
        ax.axvline(val, color="k", ls="--", lw=1.2)
        ax.set_title(f"{var} = {val:.1f}")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=7, loc="upper right")

    # aggregated output membership + defuzzified grade
    axo = axes[3]
    for label, (shape, p) in config.OUTPUT_MFS.items():
        y = trapmf(card.fuzzy.universe, *p) if shape == "trap" \
            else trimf(card.fuzzy.universe, *p)
        axo.plot(card.fuzzy.universe, y, ls=":", alpha=0.6, label=label)
    axo.fill_between(card.fuzzy.universe, card.fuzzy.aggregated,
                     alpha=0.4, color="tab:blue")
    axo.axvline(card.final_grade, color="r", lw=2,
                label=f"grade = {card.final_grade:.1f}")
    axo.set_title("Aggregated output (Mamdani) + centroid")
    axo.set_ylim(0, 1.05)
    axo.legend(fontsize=7, loc="upper right")

    fig.suptitle(f"Neuro-Symbolic Grade: {card.final_grade:.1f}/100 "
                 f"({card.letter})", fontsize=13)
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    from .grader import grade_answer
    card = grade_answer(
        "A stack is a LIFO linear data structure with push and pop.",
        "A stack is a linear data structure following Last In First Out using "
        "push and pop at the top.",
        "What is a stack?",
    )
    print(format_text(card))
