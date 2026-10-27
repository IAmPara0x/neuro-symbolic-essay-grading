# Project Build Plan
## Neuro-Symbolic Automated Essay & Answer Grading with Rule-Based Justification
### An explainable fuzzy-logic extension of Agrawal et al. (ESWA 2024, 122470)

---

## 0. The one-paragraph pitch (say this to your faculty)

> The parent paper (Agrawal et al., 2024) scores subjective answers with three NLP
> modules — keyword, semantic similarity, and NER — and fuses them with a 4-layer
> **black-box DNN**, evaluated only on RMSE. It leaves two gaps it names itself:
> the final combiner is unexplainable, and LLM/semantic integration is future work.
> This project keeps their three modules as the **symbolic + neural backbone**, but
> **replaces the opaque DNN with a transparent Mamdani fuzzy inference system** whose
> IF–THEN rule base *is* the justification. The output is not a bare mark but an
> auditable scorecard: the three module scores, the fuzzy rules that fired with their
> firing strengths, and the membership plots that produced the grade. We add
> explainability (QWK, Pearson, stability tests) the parent paper did not measure.

**Novelty in one line:** *same modules, auditable combiner.* Their DNN → your fuzzy
rule base. That single swap is the contribution; everything else is lineage.

---

## 1. How this maps onto the parent paper (keep this table in your report)

| Parent paper (Agrawal et al. 2024) | This project |
|---|---|
| Keyword module: YAKE + KeyBERT + POS + WordNet | **Reused** as symbolic keyword-coverage input |
| Similarity module: SBERT + SimCSE + cross-encoder summary | **Reused** as the neural semantic input (offline, no API) |
| NER module: spaCy / NLTK / CamemBERT, entity ∩/∪ | **Reused** as symbolic NER-overlap input |
| Fuse 3 scores with 4-layer DNN (8→16→32→64→1) | **Replaced** with Mamdani fuzzy inference (scikit-fuzzy) |
| Output = single predicted mark | Output = mark **+ rule-based justification scorecard** |
| Evaluation = RMSE only | RMSE **+ QWK + Pearson + paraphrase/padding stability + ablation** |
| Future work: "replace modules with GPT/LLMs" | Documented optional LLM module (pluggable, offline by default) |

**Decisions locked for this build:**
- Dataset: **public** — Mohler (2011) CS short-answer set (primary), ASAP-SAS (fallback).
- Symbolic pathway: **re-implement all three** parent modules.
- Neural pathway: **offline SBERT/SimCSE only** (no paid API).

---

## 2. Revised architecture (offline)

```
            ┌──────────────────────────────────────────────┐
            │  INPUT: Student Answer + Reference Answer      │
            └───────────────────────┬──────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
 [ KEYWORD MODULE ]        [ SIMILARITY MODULE ]          [ NER MODULE ]
 YAKE + KeyBERT +          SBERT / SimCSE bi-encoder       spaCy NER +
 WordNet synonyms          (+ optional cross-encoder)      CamemBERT-NER
 → coverage score 0-100    → semantic score 0-100          → entity overlap 0-100
        │                           │                           │
        │              (+ optional mechanical metrics:          │
        │               word count, grammar errors,             │
        │               syntactic depth via spaCy/LT)           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │   MAMDANI FUZZY INFERENCE      │  ← replaces the DNN
                    │  fuzzify → IF-THEN rules →     │
                    │  aggregate → centroid defuzz   │
                    └───────────────┬───────────────┘
                                    ▼
             ┌──────────────────────────────────────────────┐
             │  OUTPUT: Final grade + EXPLAINABLE SCORECARD  │
             │  module scores · fired rules + strengths ·    │
             │  membership plots · (optional LLM rationale)  │
             └──────────────────────────────────────────────┘
```

**Note on "neural":** the SBERT/SimCSE transformer *is* your neural component — it is a
deep network doing semantic judgment that rules cannot. You do not need an LLM to be
neuro-symbolic. Update `source/architecture.png` and `report.tex` to this version.

---

## 3. Repository layout

```
neuro-symbolic-essay-grading/
├── data/
│   ├── raw/                  # downloaded Mohler / ASAP-SAS
│   └── processed/            # normalized: question, ref_answer, student_answer, human_score
├── src/
│   ├── config.py             # thresholds, model names, grade scale, paths
│   ├── preprocess.py         # contraction expansion, lowering, punctuation strip (mirror paper Fig.1)
│   ├── modules/
│   │   ├── keyword.py        # YAKE + KeyBERT + WordNet → coverage score
│   │   ├── similarity.py     # SBERT + SimCSE cosine, threshold logic → semantic score
│   │   ├── ner.py            # spaCy + CamemBERT entities, ∩/∪ → NER score
│   │   └── mechanics.py      # (optional) word count, grammar errors, dependency depth
│   ├── fuzzy_engine.py       # membership functions + rule base + inference + fired-rule trace
│   ├── grader.py             # orchestrates modules → fuzzy → scorecard dict
│   └── scorecard.py          # builds explanation object + matplotlib membership plots
├── app/
│   └── streamlit_app.py      # paste answers, press Grade, show scorecard
├── eval/
│   ├── run_eval.py           # QWK, Pearson, RMSE on dataset
│   ├── ablation.py           # each-module-only vs full system vs mean-baseline
│   └── robustness.py         # paraphrase + padding stability tests
├── tests/                    # unit tests per module (deterministic scores)
├── notebooks/                # EDA + fuzzy-rule tuning scratch
├── requirements.txt
└── README.md
```

---

## 4. Build phases (6 weeks, matches your slides' timeline)

### Phase 0 — Scaffolding (half day)
- `python -m venv venv`; create `requirements.txt`:
  `spacy, nltk, yake, keybert, sentence-transformers, scikit-fuzzy, numpy,
   scipy, scikit-learn, pandas, matplotlib, streamlit, transformers, torch`.
- `python -m spacy download en_core_web_sm`; download NLTK `wordnet`, `punkt`.
- Commit the empty structure. No API keys needed (offline).

### Phase 1 — Data (Week 1)
- Download **Mohler (2011)** short-answer grading dataset (CS "Data Structures" course;
  ~2273 student answers, 80 questions, reference answers, averaged grades 0–5).
  Fallback: **ASAP-SAS** (Kaggle, 10 prompts, integer scores).
- Write `preprocess.py` to normalize into one schema:
  `{question, reference_answer, student_answer, human_score}`.
- Rescale human scores to **0–100** (or your chosen grade scale) for consistency with
  module outputs. Keep original scale column for RMSE-vs-paper comparison.
- Hold out a fixed test split (seed it) so eval is reproducible.

### Phase 2 — Symbolic + neural modules (Weeks 2–3)
Implement each module to return a **normalized 0–100 score + a raw-evidence dict**
(the evidence is what the scorecard shows). Mirror the parent paper's methods:

- **`keyword.py`** — extract keywords from reference with YAKE *and* KeyBERT; POS-tag
  the student answer; expand with WordNet synonyms; score = matched / expected coverage.
  Evidence: matched keywords, missed keywords.
- **`similarity.py`** — encode reference and student with SBERT (`all-MiniLM-L6-v2`) and
  SimCSE; cosine similarity; apply the paper's 0.75 threshold logic; optional
  cross-encoder re-rank. Evidence: cosine value, per-sentence best matches.
- **`ner.py`** — extract entities + cardinal values with spaCy and CamemBERT-NER;
  score = |common| / |union| (paper's ∩/∪ with 0.9 cardinal threshold).
  Evidence: common entities, missing entities.
- **`mechanics.py`** *(optional but recommended for a richer fuzzy input)* — word count,
  grammar-error count (`language-tool-python`), mean dependency depth. These give the
  fuzzy engine a "mechanical correctness" axis the parent paper lacked.
- **Unit-test** each module on 2–3 hand-made answer pairs with expected score ranges.

### Phase 3 — Fuzzy inference engine (Week 4) — *the core contribution*
- In `fuzzy_engine.py` define, with **scikit-fuzzy**:
  - Inputs (`Antecedent`): `keyword`, `similarity`, `ner` (+ optional `mechanics`),
    each 0–100 with triangular MFs **Low / Medium / High**.
  - Output (`Consequent`): `grade` 0–100 with MFs **Poor / Average / Good / Excellent**.
  - A small, **printable** rule base encoding the examiner's policy, e.g.:
    - IF similarity High AND keyword High → Excellent
    - IF keyword High AND similarity Low → Average  *(right terms, no understanding)*
    - IF similarity High AND keyword Low → Good  *(understands, imprecise wording)*
    - IF ner Low AND keyword Low AND similarity Low → Poor
  - Mamdani inference + **centroid** defuzzification.
- **Expose the trace**: after `ControlSystemSimulation.compute()`, record each rule's
  firing strength so the scorecard can list *which rules fired and how strongly*. This
  is the feature the DNN cannot provide — build it deliberately, don't skip it.
- Provide **two rule sets** (strict vs lenient) toggled in config, to show the policy is
  editable without touching code — a talking point for the demo.

### Phase 4 — Scorecard + Streamlit UI (Week 5)
- `scorecard.py`: assemble `{module_scores, evidence, fired_rules, final_grade}` and
  render membership plots (`skfuzzy` view + matplotlib) to PNG/figure.
- `streamlit_app.py`: two text boxes (student / reference) + question field → **Grade**
  button → show module scores, matched/missed keywords & entities, cosine value, the
  fired-rule table, and the aggregated output-membership plot with the defuzzified mark.
- This is your live demo. Make it load models once (cache) so grading is fast.

### Phase 5 — Evaluation (Week 6)
Run on the held-out split and tabulate:
- **Agreement:** Quadratic Weighted Kappa, Pearson r, **and RMSE** (RMSE lets you put
  your number next to the parent paper's ~0.033–0.039, with the caveat of different data).
- **Ablation** (`ablation.py`): keyword-only, similarity-only, ner-only, mean-baseline,
  vs full fuzzy system → shows each module's contribution, like the paper's module study.
- **Robustness** (`robustness.py`) — *tests the parent paper never ran*:
  - *Paraphrase stability:* paraphrase student answers (back-translation or synonym swap),
    measure grade drift. Expect small drift → sign of a stable grader.
  - *Padding attack:* append irrelevant filler, check the grade does **not** rise →
    demonstrates resistance to the length-gaming AES is known for.
- **Explainability** is argued qualitatively: show one fully worked scorecard where the
  explanation *is* the computation, not a post-hoc story.

---

## 5. What to change in your existing report/slides

Your current `report.tex` is well written but has two things to fix:
1. **It never cites the parent paper.** Add Agrawal et al. (2024) as `\cite{agrawal2024}`
   in Related Work and frame Section 1.4/Positioning explicitly as *extending* it (use
   the Section 1 table above). This is the single most important edit.
2. **It assumes an LLM API.** Since you chose offline SBERT, rewrite the "constrained LLM
   / hallucination / JSON" passages: the neural component is now the SBERT/SimCSE
   transformer, and the anti-hallucination/explainability argument moves entirely to the
   **fuzzy layer replacing the DNN**. Keep the optional LLM module as one future-work line.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| CamemBERT-NER is French-trained; weak on English CS entities | Use spaCy `en_core_web_sm`/`trf` as primary NER; cite CamemBERT as the paper's choice and note the swap. |
| SBERT similarity and keyword overlap are correlated → fuzzy inputs redundant | Keep NER + mechanics axes to add independent signal; report input correlation in eval. |
| Fuzzy rules feel hand-tuned / arbitrary | Document the rule base explicitly (it's a *feature*), and show strict-vs-lenient toggle; justify thresholds from the data distribution. |
| Public dataset ≠ paper's dataset, so RMSE isn't directly comparable | State this plainly; lean on QWK/Pearson/robustness as the real contribution, RMSE as context. |
| scikit-fuzzy centroid is slow for many inputs | Keep ≤4 fuzzy inputs; precompute the control system once, reuse the simulation object. |

---

## 7. Deliverables checklist
- [ ] Working Streamlit demo that grades a pasted answer live with a full scorecard.
- [ ] Printable, editable fuzzy rule base (strict + lenient).
- [ ] Eval table: full system vs ablations vs baseline (QWK, Pearson, RMSE).
- [ ] Robustness results: paraphrase drift + padding resistance.
- [ ] Updated report that cites and extends Agrawal et al. (2024) with the mapping table.
- [ ] Updated `architecture.png` matching the offline design in §2.
```
```
```

**Immediate next steps:** Phase 0 scaffolding + Phase 1 data download. Say the word and
I'll create the repo structure, `requirements.txt`, and the preprocessing script.
