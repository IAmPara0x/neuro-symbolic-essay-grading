% Neuro-Symbolic Automated Essay/Answer Grading
% with Rule-Based Justification
% Sahil Barnwal (24BDS0256) — extending Agrawal et al., ESWA 239 (2024)

## The Problem

- Hand grading long answers is slow and inconsistent.
- The parent paper (Agrawal et al., 2024) grades well but fuses its
  three NLP modules with a **black-box DNN**.
- The mark has no trace back to the evidence.
- When a student contests a grade, there is nothing auditable to show.
- A mark we cannot defend is not usable.

## The Idea

- Keep the parent paper's three modules as the **evidence**.
- Replace the opaque DNN with a **fuzzy IF-THEN rule base**.
- The rule base *is* the justification — the rules that fired *are* the explanation.
- Neural part = offline sentence embeddings (a sensor, not the judge).
- Output: a grade **plus** the rules and evidence behind it.

## Extends the Parent Paper, Point for Point

| Parent paper (ESWA 2024) | This project |
|--------------------------|--------------|
| Keyword: YAKE + KeyBERT + WordNet | Reused (symbolic) |
| Similarity: SBERT / SimCSE | Reused (neural, offline) |
| NER: spaCy / CamemBERT | Reused (symbolic) |
| Fuse 3 scores with 4-layer DNN | **Fuzzy rule base** |
| Output: one number | Output: number + scorecard |
| Evaluation: RMSE only | + QWK, Pearson, stability |

## System Architecture

![](architecture.png){height=3.6in}

## Step 1 - Data

- Public **Mohler (2011) UNT CS short-answer** corpus.
- 2,273 student answers, 79 questions, reference answer each.
- Human grades 0-5 (two annotators), rescaled to 0-100.
- Matches the parent paper's computer-science domain.

## Step 2 - Symbolic Pathway (reused modules)

- **Keyword:** YAKE + KeyBERT on the reference, WordNet synonym
  expansion, coverage of reference keywords.
- **NER:** spaCy entities + numbers/big-O, Jaccard overlap.
- **Mechanics:** length adequacy, grammar errors, syntactic depth
  (advisory penalty only — the axis the parent paper lacked).
- Every metric normalised to 0-100, fully reproducible.

## Step 3 - Neural Pathway (offline)

- Sentence-BERT (`all-MiniLM-L6-v2`), runs locally — no API.
- Encodes student and reference, cosine similarity.
- Per-sentence coverage against the reference (0.75 threshold).
- One deterministic number → nothing to hallucinate.
- This is the only neural component: a semantic **sensor**.

## Step 4 - Fuzzy Engine: Setup

- Inputs: keyword, similarity, NER scores (the 3 parent modules).
- Output: final grade.
- Triangular / trapezoidal membership functions: Low, Medium, High.
- Each score gets a degree of membership in each set.

## Step 4 - Fuzzy Engine: Rules

- IF similarity High AND keyword High THEN Excellent.
- IF keyword High AND similarity Low THEN Average.
    - the right terms, no real understanding
- IF similarity High AND keyword Low THEN Good.
    - weak wording, strong ideas
- Mamdani inference, then centroid defuzzification.
- Strict / lenient policy = just a different rule set (no code change).

## Step 5 - Scorecard and UI

- Streamlit page: paste both answers, press Grade.
- Show raw metrics: keyword coverage, cosine, entities, errors.
- Show the semantic score separately.
- **List which rules fired and how strongly.**
- Plot the membership functions and the aggregated output.

## Step 6 - Evaluation

- Compare system marks against human marks on all 2,273 answers.
- Metrics: Quadratic Weighted Kappa, Pearson, RMSE.
- Ablation: each module alone vs linear mean vs full fuzzy.
- Paraphrase test: does the grade stay stable?
- Padding test: does filler text raise the grade?

## Results — Fuzzy Combiner Wins on Agreement

| System | RMSE | Pearson | QWK |
|--------|------|---------|-----|
| mean-baseline | 21.9 | 0.00 | 0.00 |
| similarity-only | 34.9 | **0.50** | 0.26 |
| mean-of-modules | 33.1 | 0.44 | 0.25 |
| **full-fuzzy (lenient)** | 34.2 | 0.48 | **0.31** |

- **Best QWK of any configuration** — beats every single module and
  the linear average.
- After one affine calibration: held-out RMSE **19.9** < baseline 21.9.

## Results — Stability (what the DNN was never tested for)

- **Paraphrase:** grade moves only **0.72 pts** on average.
- **Padding:** appending filler changes the grade by **-1.1 pts**.
    - the system does *not* reward verbosity — resists length-gaming.
- Stability follows from the architecture: a centroid over a small
  rule base changes smoothly with its inputs.

## Tech Stack

| Part | Tool |
|------|------|
| Parsing, POS, NER | spaCy |
| Keywords | YAKE + KeyBERT + WordNet |
| Semantic judgement | Sentence-BERT (offline) |
| Fuzzy inference | from-scratch Mamdani (NumPy) |
| Interface | Streamlit |
| Plots | matplotlib |

## Why This Is Neuro-Symbolic

- Neural: the SBERT transformer handles meaning.
- Symbolic: keyword, NER and mechanics give checkable facts.
- Fuzzy rules make the actual decision.
- The neural model is a **sensor, not the judge**.
- A single weak/wrong input cannot move the mark on its own.

## Why a Fuzzy Engine Instead of the DNN?

- The rule base is **readable and editable** by the examiner.
- It encodes **non-linear policies** a weighted sum cannot
  (e.g. right terms + no understanding → Average).
- Every rule's firing strength is exposed → the explanation **is**
  the computation, not a story about it.
- No training, no black box, no hallucinated justification.

## Deliverables

- Streamlit demo, graded live during the review.
- Documented rule base the examiner can edit (strict / lenient).
- Benchmark: our system vs each module vs linear mean vs human.
- Full project report (17 pp) extending the parent paper, with
  real results and figures.
