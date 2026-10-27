"""Full benchmark on the Mohler (2011) UNT CS short-answer dataset.

Produces everything the paper needs, written to results/:
  * metrics.json          -- all systems x {RMSE, Pearson, QWK}
  * ablation_table.md     -- the main results table
  * robustness.json       -- paraphrase stability + padding resistance
  * calibration.json      -- optional affine calibration (train/test), honest RMSE
  * fig_scatter.png       -- predicted vs human (full system)
  * fig_distribution.png  -- human vs predicted grade distributions
  * fig_ablation.png      -- QWK by system
  * fig_membership.png    -- fuzzy input/output membership functions

The core grader is training-free (fixed fuzzy rules), so primary metrics are
reported on the full dataset. A separate, clearly-labelled affine calibration
(fit on 80% train, evaluated on 20% test) is included only to report an
apples-to-closer RMSE against the parent paper's trained DNN.

Run:  python -m eval.benchmark
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402

from src import config                                           # noqa: E402
from src.preprocess import load_dataset, normalise               # noqa: E402
from src.grader import Grader                                    # noqa: E402
from src.fuzzy_engine import FuzzyGrader, trimf, trapmf          # noqa: E402
from src.modules import keyword, similarity, ner, mechanics      # noqa: E402
from eval.run_eval import rmse, pearson, quadratic_weighted_kappa  # noqa: E402

RESULTS = config.ROOT / "results"
DATASET = config.DATA_PROCESSED / "mohler.csv"


def _metrics(pred, true):
    pred, true = np.asarray(pred, float), np.asarray(true, float)
    return {
        "rmse_0_100": round(rmse(pred, true), 2),
        "rmse_norm": round(rmse(pred / 100, true / 100), 4),
        "pearson": round(pearson(pred, true), 3),
        "qwk": round(quadratic_weighted_kappa(pred, true), 3),
    }


def collect(df):
    """Grade every row once; return module scores + fuzzy grades for both policies."""
    fz_strict = FuzzyGrader("strict")
    fz_lenient = FuzzyGrader("lenient")
    kw, sim, nr, mech = [], [], [], []
    full_s, full_l = [], []

    t = time.time()
    for i, row in enumerate(df.itertuples()):
        s, r = normalise(row.student_answer), normalise(row.reference_answer)
        k = keyword.score(s, r).score
        sm = similarity.score(s, r).score
        n = ner.score(s, r).score
        m = mechanics.score(s, r).score
        kw.append(k); sim.append(sm); nr.append(n); mech.append(m)

        inp = {"keyword": k, "similarity": sm, "ner": n}
        pen = config.MECHANICS_PENALTY_WEIGHT * (100.0 - m)
        full_s.append(float(np.clip(fz_strict.grade(inp).grade - pen, 0, 100)))
        full_l.append(float(np.clip(fz_lenient.grade(inp).grade - pen, 0, 100)))
        if (i + 1) % 500 == 0:
            print(f"  graded {i+1}/{len(df)}  ({(time.time()-t):.0f}s)")

    return {k: np.array(v) for k, v in dict(
        keyword=kw, similarity=sim, ner=nr, mechanics=mech,
        full_strict=full_s, full_lenient=full_l).items()}


def run():
    RESULTS.mkdir(exist_ok=True)
    df = load_dataset(DATASET)
    true = df["human_score"].to_numpy()
    print(f"Dataset: {len(df)} answers, {df['question'].nunique()} questions, "
          f"human mean {true.mean():.1f}/100")

    sc = collect(df)

    systems = {
        "mean-baseline":    np.full_like(true, true.mean()),
        "keyword-only":     sc["keyword"],
        "similarity-only":  sc["similarity"],
        "ner-only":         sc["ner"],
        "mean-of-modules":  (sc["keyword"] + sc["similarity"] + sc["ner"]) / 3.0,
        "full-fuzzy-lenient": sc["full_lenient"],
        "full-fuzzy-strict":  sc["full_strict"],
    }
    metrics = {name: _metrics(pred, true) for name, pred in systems.items()}

    # ---- optional affine calibration (train/test), clearly separate ----------
    # Primary system = lenient policy: it matches this dataset's lenient human
    # graders (mean 4.18/5) and achieves the best QWK in the ablation.
    primary = sc["full_lenient"]
    rng = np.random.default_rng(42)
    idx = rng.permutation(len(df))
    cut = int(0.8 * len(df))
    tr, te = idx[:cut], idx[cut:]
    x = primary
    a, b = np.polyfit(x[tr], true[tr], 1)              # fit on train only
    cal_pred = a * x[te] + b
    calibration = {
        "fit": {"slope": round(float(a), 3), "intercept": round(float(b), 2)},
        "train_n": int(len(tr)), "test_n": int(len(te)),
        "uncalibrated_test": _metrics(x[te], true[te]),
        "calibrated_test": _metrics(cal_pred, true[te]),
    }

    # ---- robustness (subset for speed) ---------------------------------------
    robustness = run_robustness(df, n=400)

    # ---- write results -------------------------------------------------------
    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (RESULTS / "calibration.json").write_text(json.dumps(calibration, indent=2))
    (RESULTS / "robustness.json").write_text(json.dumps(robustness, indent=2))
    write_table(metrics)

    # ---- figures -------------------------------------------------------------
    fig_scatter(primary, true)
    fig_distribution(primary, true)
    fig_ablation(metrics)
    fig_membership()

    print("\n=== MAIN RESULTS (full dataset) ===")
    print(f"{'system':<20}{'rmse':>8}{'pearson':>10}{'qwk':>8}")
    for name, m in metrics.items():
        print(f"{name:<20}{m['rmse_0_100']:>8}{m['pearson']:>10}{m['qwk']:>8}")
    print(f"\nCalibrated (test) RMSE: "
          f"{calibration['calibrated_test']['rmse_0_100']} "
          f"(uncalibrated {calibration['uncalibrated_test']['rmse_0_100']})")
    print(f"Robustness: paraphrase drift {robustness['paraphrase_mean_abs_drift']} pts, "
          f"padding change {robustness['padding_mean_grade_change']} pts")
    print(f"\nAll results + figures written to {RESULTS}/")


def run_robustness(df, n=400):
    from eval.robustness import paraphrase, _FILLER
    grader = Grader()
    sub = df.sample(min(n, len(df)), random_state=7)
    base, para, pad = [], [], []
    for row in sub.itertuples():
        b = grader.grade(row.student_answer, row.reference_answer, row.question).final_grade
        p = grader.grade(paraphrase(row.student_answer), row.reference_answer, row.question).final_grade
        d = grader.grade(row.student_answer + _FILLER, row.reference_answer, row.question).final_grade
        base.append(b); para.append(p); pad.append(d)
    base, para, pad = map(np.array, (base, para, pad))
    return {
        "n": int(len(sub)),
        "paraphrase_mean_abs_drift": round(float(np.mean(np.abs(para - base))), 2),
        "paraphrase_max_abs_drift": round(float(np.max(np.abs(para - base))), 2),
        "padding_mean_grade_change": round(float(np.mean(pad - base)), 2),
        "padding_pct_increased": round(100.0 * float(np.mean(pad > base + 1e-6)), 1),
    }


def write_table(metrics):
    lines = ["| System | RMSE (0-100) | Pearson r | QWK |", "|---|---|---|---|"]
    for name, m in metrics.items():
        lines.append(f"| {name} | {m['rmse_0_100']} | {m['pearson']} | {m['qwk']} |")
    (RESULTS / "ablation_table.md").write_text("\n".join(lines) + "\n")


def fig_scatter(pred, true):
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.scatter(true, pred, s=10, alpha=0.25, color="tab:blue", edgecolors="none")
    a, b = np.polyfit(true, pred, 1)
    xs = np.linspace(0, 100, 50)
    ax.plot(xs, a * xs + b, "r-", lw=1.5, label=f"fit (r={pearson(pred, true):.2f})")
    ax.plot([0, 100], [0, 100], "k--", lw=0.8, alpha=0.5, label="ideal")
    ax.set_xlabel("Human score (0-100)"); ax.set_ylabel("System grade (0-100)")
    ax.set_title("Predicted vs human (full neuro-symbolic system)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(RESULTS / "fig_scatter.png", dpi=130); plt.close(fig)


def fig_distribution(pred, true):
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    bins = np.linspace(0, 100, 21)
    ax.hist(true, bins=bins, alpha=0.6, label="human", color="tab:green")
    ax.hist(pred, bins=bins, alpha=0.6, label="system", color="tab:blue")
    ax.set_xlabel("Grade (0-100)"); ax.set_ylabel("Count")
    ax.set_title("Grade distribution: human vs system")
    ax.legend(fontsize=9); fig.tight_layout()
    fig.savefig(RESULTS / "fig_distribution.png", dpi=130); plt.close(fig)


def fig_ablation(metrics):
    names = list(metrics.keys())
    qwk = [metrics[n]["qwk"] for n in names]
    pear = [metrics[n]["pearson"] for n in names]
    x = np.arange(len(names)); w = 0.38
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.bar(x - w/2, qwk, w, label="QWK", color="tab:blue")
    ax.bar(x + w/2, pear, w, label="Pearson r", color="tab:orange")
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Agreement"); ax.set_title("Ablation: contribution of each component")
    ax.legend(fontsize=9); fig.tight_layout()
    fig.savefig(RESULTS / "fig_ablation.png", dpi=130); plt.close(fig)


def fig_membership():
    x = np.linspace(0, 100, 501)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    for label, (shape, p) in config.INPUT_MFS.items():
        y = trapmf(x, *p) if shape == "trap" else trimf(x, *p)
        a1.plot(x, y, label=label)
    a1.set_title("Input membership (keyword / similarity / ner)")
    a1.set_ylim(0, 1.05); a1.legend(fontsize=8)
    for label, (shape, p) in config.OUTPUT_MFS.items():
        y = trapmf(x, *p) if shape == "trap" else trimf(x, *p)
        a2.plot(x, y, label=label)
    a2.set_title("Output membership (grade)")
    a2.set_ylim(0, 1.05); a2.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(RESULTS / "fig_membership.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    run()
