# Neuro-Symbolic Automated Essay & Answer Grading with Rule-Based Justification

An explainable grading system that fuses three NLP modules — **keyword**, **semantic
similarity**, and **NER** — with a transparent **Mamdani fuzzy inference engine**.
Unlike a black-box grader, every mark comes with the exact rules that produced it.

> **Extension of** Agrawal, Mishra, Kandasamy, Terni & Vasantha,
> *"Revolutionizing subjective assessments: A three-pronged comprehensive approach
> with NLP and deep learning,"* Expert Systems With Applications 239 (2024) 122470.
> That paper fuses the same three modules with an **opaque 4-layer DNN** and reports
> only RMSE. **This project replaces the DNN with an auditable fuzzy rule base** (the
> rule base *is* the justification), adds explainability, and evaluates stability.
> See [`PROJECT_PLAN.md`](PROJECT_PLAN.md) for the full design rationale.

---

## What it does

```
Student answer + Reference answer
        │
        ├── KEYWORD module      (symbolic)  YAKE + KeyBERT + WordNet   → 0–100
        ├── SIMILARITY module   (neural)    SBERT / SimCSE cosine      → 0–100
        ├── NER module          (symbolic)  spaCy entities ∩/∪         → 0–100
        └── MECHANICS module    (advisory)  length / grammar / depth   → 0–100
                            │
                MAMDANI FUZZY INFERENCE  (replaces the DNN)
                fuzzify → IF-THEN rules → aggregate → centroid
                            │
          Final grade + EXPLAINABLE SCORECARD
          (module scores · fired rules + strengths · membership plots)
```

The **neural** component is the SBERT/SimCSE transformer — it judges meaning, which
rules cannot. Everything else is symbolic and independently verifiable. The fuzzy
engine owns the final decision, so a wrong module score cannot silently set the mark.

## Quick start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt')"
```

The project **runs without the heavy models too** — if SBERT/spaCy/YAKE are missing,
each module falls back (TF-IDF cosine, regex NER, frequency keywords) so the pipeline
never breaks. Install the full stack for the real numbers.

### Grade one answer (CLI)
```bash
python -m src.grader        # JSON scorecard for a built-in example
python -m src.scorecard     # human-readable justification transcript
```

### Launch the demo UI
```bash
streamlit run app/streamlit_app.py
```
Paste a student answer + reference answer, press **Grade**, and see module scores,
the fuzzy rules that fired with their strengths, the evidence, and the membership
plots. A strict/lenient policy toggle shows the rule base is editable without code.

### Benchmark on the real dataset (Mohler 2011, 2,273 CS short answers)
```bash
# one-time: download + unzip ShortAnswerGrading_v2.0 into data/raw/mohler_extracted/
python -m src.datasets       # build data/processed/mohler.csv (2,273 answers)
python -m eval.benchmark     # full benchmark → results/ (tables + figures + JSON)
```

### Quick evaluate (on the bundled sample set)
```bash
python -m eval.run_eval      # RMSE, Pearson r, Quadratic Weighted Kappa
python -m eval.ablation      # each module alone vs mean-of-modules vs full fuzzy
python -m eval.robustness    # paraphrase stability + padding-attack resistance
python tests/test_pipeline.py   # unit tests (or: python -m pytest -q)
```

## Results on Mohler (2011) — 2,273 CS short answers, full dataset

| System | RMSE (0–100) | Pearson r | QWK |
|---|---|---|---|
| mean-baseline | 21.93 | 0.000 | 0.000 |
| keyword-only | 51.91 | 0.469 | 0.177 |
| similarity-only (neural, cross-encoder) | 36.33 | 0.554 | 0.248 |
| ner-only | 42.45 | 0.068 | 0.063 |
| mean-of-modules (linear, 3 modules) | 33.83 | 0.446 | 0.251 |
| mean(keyword+similarity) (linear, same inputs) | 42.83 | 0.539 | 0.209 |
| full-fuzzy (strict) | 42.35 | 0.552 | 0.244 |
| **full-fuzzy (lenient), uncalibrated** | 35.33 | 0.551 | 0.315 |
| **full-fuzzy (lenient) + calibration** | **17.65** | **0.594** | **0.459** |

The fuzzy combiner achieves the **highest QWK of any configuration**, and beats a linear
average of the *same two inputs* (0.315 vs 0.209) — the rule base itself adds the gain.
Held-out (isotonic calibration, fit on 80% train, eval on 20% test): **QWK 0.481,
Pearson 0.612, RMSE 17.99**, beating the mean-prediction baseline (21.93).

**Robustness:** paraphrase mean drift **0.24 pts** (very stable); appending filler
changes the grade by **−0.5 pts** on average — the system does **not** reward verbosity.

> Three improvements over the first version: (1) NER dropped from the fuzzy decision
> (empirically near-random here, r=0.07; still shown as evidence); (2) a **cross-encoder**
> for the semantic pair score (Pearson 0.48 → 0.55); (3) reshaped output sets + **isotonic
> calibration** (QWK 0.38 → 0.48, RMSE 19.9 → 18.0 on held-out test).

> The dataset is strongly skewed to high marks (human mean 83.7/100), which makes the
> constant mean-baseline hard to beat on RMSE alone — hence rank metrics (QWK, Pearson)
> are primary. The contribution is **architectural** (auditable combiner +
> explainability + stability), not a SOTA accuracy figure. Full write-up and figures:
> [`source/report.tex`](source/report.tex) → `report.pdf`.

## Project layout

| Path | Role |
|---|---|
| `src/config.py` | thresholds, model names, membership-function params, policy |
| `src/preprocess.py` | normalisation + dataset loader (sample / Mohler / ASAP) |
| `src/datasets.py` | Mohler (2011) → canonical CSV converter |
| `src/modules/keyword.py` | YAKE + KeyBERT + WordNet coverage (symbolic) |
| `src/modules/similarity.py` | SBERT / SimCSE semantic score (**neural**) |
| `src/modules/ner.py` | spaCy entity overlap (symbolic) |
| `src/modules/mechanics.py` | length / grammar / syntactic depth (advisory) |
| `src/fuzzy_engine.py` | **self-contained Mamdani FIS with per-rule firing-strength trace** |
| `src/grader.py` | orchestration → `Scorecard` |
| `src/scorecard.py` | text transcript + membership-function plots |
| `app/streamlit_app.py` | interactive demo |
| `eval/` | `run_eval` · `ablation` · `robustness` · `benchmark` (full Mohler run) |
| `results/` | benchmark tables, JSON metrics, and paper figures |
| `tests/` | deterministic unit tests |

## Design notes

- **Why a from-scratch fuzzy engine, not scikit-fuzzy?** The justification requires the
  *firing strength of every rule*, which scikit-fuzzy does not expose cleanly. The
  engine in `fuzzy_engine.py` is a standard Mamdani FIS (triangular MFs, min/max,
  centroid) that returns the full trace. scikit-fuzzy is still listed as a dependency
  for the equivalent reference implementation.
- **CamemBERT note:** the parent paper used CamemBERT-NER, which is French-trained;
  for English CS answers spaCy is the primary NER backend (see `PROJECT_PLAN.md`).
- **No API / fully offline:** the neural pathway is local SBERT, so there is nothing to
  hallucinate and no key to manage. An LLM module can be slotted in later behind the
  same `ModuleResult` interface.

## Author
Sahil Barnwal (24BDS0256) — Artificial Intelligence course project.
