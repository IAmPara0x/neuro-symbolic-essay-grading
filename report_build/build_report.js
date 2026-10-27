// Builds Team35_BCSE306_FinalReview.docx from the project's real content + results.
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  Footer, PageNumber, TableOfContents, ImageRun, PageBreak, LevelFormat,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "results");
const img = (f) => fs.readFileSync(path.join(FIG, f));

const FONT = "Times New Roman";
const USABLE = 9026; // A4 width (11906) - 2*1440 margins

// ---------- helpers ----------
function runs(parts) {
  // parts: array of [text, {bold,italic,...}] or plain string
  return parts.map((p) =>
    typeof p === "string"
      ? new TextRun({ text: p, font: FONT, size: 24 })
      : new TextRun({ text: p[0], font: FONT, size: 24, ...(p[1] || {}) })
  );
}
function P(text, opts = {}) {
  const children = Array.isArray(text) ? runs(text) : runs([text]);
  return new Paragraph({
    children,
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: opts.after != null ? opts.after : 120 },
    ...opts.extra,
  });
}
function bullet(text, level = 0) {
  const children = Array.isArray(text) ? runs(text) : runs([text]);
  return new Paragraph({
    children, bullet: { level },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 360, after: 60 },
  });
}
function numbered(text, ref) {
  const children = Array.isArray(text) ? runs(text) : runs([text]);
  return new Paragraph({
    children, numbering: { reference: ref, level: 0 },
    alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 60 },
  });
}
function H1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: FONT, size: 32, bold: true, color: "1F3864" })],
    spacing: { before: 280, after: 140 }, keepNext: true });
}
function H2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: FONT, size: 28, bold: true, color: "2E4A7A" })],
    spacing: { before: 200, after: 100 }, keepNext: true });
}
function H3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, font: FONT, size: 24, bold: true })],
    spacing: { before: 160, after: 80 }, keepNext: true });
}
function caption(text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 160 },
    children: [new TextRun({ text, font: FONT, size: 20, italics: true })] });
}
function note(text) {
  return new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, after: 120 },
    children: [new TextRun({ text, font: FONT, size: 22, italics: true, color: "B00000" })] });
}
function cell(content, w, { bold = false, fill = null, align = AlignmentType.LEFT, size = 20 } = {}) {
  const paras = (Array.isArray(content) ? content : [content]).map(
    (t) => new Paragraph({ alignment: align, spacing: { line: 276, after: 20 },
      children: [new TextRun({ text: t, font: FONT, size, bold })] }));
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: paras,
  });
}
function table(headers, rows, widths, { headFill = "D9E2F3", fontSize = 20 } = {}) {
  const headRow = new TableRow({ tableHeader: true,
    children: headers.map((h, i) => cell(h, widths[i], { bold: true, fill: headFill, size: fontSize })) });
  const bodyRows = rows.map((r) => new TableRow({
    children: r.map((c, i) => cell(c, widths[i], { size: fontSize })) }));
  return new Table({
    width: { size: USABLE, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headRow, ...bodyRows],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "BBBBBB" },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "BBBBBB" },
    },
  });
}
function figure(file, wpx, hpx, cap) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 20 },
      children: [new ImageRun({ type: "png", data: img(file), transformation: { width: wpx, height: hpx } })] }),
    caption(cap),
  ];
}
function spacer() { return new Paragraph({ spacing: { after: 80 }, children: [] }); }

// ---------- build content ----------
const content = [];
const add = (...xs) => xs.forEach((x) => content.push(x));

// ===== TITLE PAGE =====
add(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 80 },
    children: [new TextRun({ text: "BCSE306 — ARTIFICIAL INTELLIGENCE", font: FONT, size: 28, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "Final Project Review Report", font: FONT, size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 120 },
    children: [new TextRun({ text: "Neuro-Symbolic Automated Essay and Answer Grading with Rule-Based Justification",
      font: FONT, size: 36, bold: true, color: "1F3864" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "A Fuzzy-Logic Framework that Replaces the Black-Box Combiner of a Three-Module NLP Grader with an Auditable Rule Base",
      font: FONT, size: 24, italics: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
    children: [new TextRun({ text: "Primary Track: E — Neuro-Symbolic, Fuzzy and Neutrosophic Reasoning    |    Secondary Track: F — Applied AI Systems",
      font: FONT, size: 22, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({ text: "Team No.: 35", font: FONT, size: 22, bold: true })] }),
);
add(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [new TextRun({ text: "Team Members (maximum three)", font: FONT, size: 22, bold: true })] }),
  table(
    ["Reg. No.", "Name", "Primary role in the project"],
    [
      ["24BDS0256", "Sahil Barnwal", "Full system: symbolic & neural modules, fuzzy engine, evaluation, report"],
      ["[24XXX0000]", "[Name — if applicable]", "[role]"],
      ["[24XXX0000]", "[Name — if applicable]", "[role]"],
    ],
    [1900, 2800, 4326], { fontSize: 20 }),
  spacer(),
);
add(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 40 },
    children: [new TextRun({ text: "Report submitted for the Final Project Review of", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "Course Code: BCSE306 — Artificial Intelligence    |    Slot: D1", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "Professor: Dr. Ilanthenral Kandasamy", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "GitHub Repository: [INSERT REPOSITORY URL]", font: FONT, size: 22, bold: true, color: "B00000" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 20 },
    children: [new TextRun({ text: "Vellore Institute of Technology, Vellore", font: FONT, size: 22, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Fall Semester 2026–27  |  October 2026", font: FONT, size: 22 })] }),
  new Paragraph({ children: [new PageBreak()] }),
);

// ===== DECLARATION =====
add(H1("Declaration and Individual Contribution"));
add(P("We declare that this report and the accompanying code are our own work, carried out for BCSE306 Artificial Intelligence during Fall Semester 2026–27. All sources, datasets, pre-trained models and AI tools used have been acknowledged. Every reference cited has been personally checked by us. We understand that each of us may be examined individually on any part of this work during the viva."));
add(table(
  ["Reg. No.", "Name", "Modules / components owned", "Report sections written", "Contribution (%)", "Signature"],
  [
    ["24BDS0256", "Sahil Barnwal", "Symbolic modules (keyword/NER/mechanics), SBERT neural module, Mamdani fuzzy engine, Streamlit UI, evaluation & benchmark scripts", "All (1–12)", "100", ""],
    ["", "", "", "", "", ""],
    ["", "", "", "", "", ""],
  ],
  [1300, 1500, 2626, 1500, 1100, 1000], { fontSize: 18 }));
add(note("Note: complete the remaining rows if the team has more than one member; contributions must total 100%, each member must sign, and each must be able to defend the whole system in the viva."));
add(new Paragraph({ children: [new PageBreak()] }));

// ===== ABSTRACT =====
add(H1("Abstract"));
add(P("Automated grading of subjective answers has shifted from hand-engineered features to neural models that read an answer and emit a grade in one pass. The work this project extends — Agrawal et al. (Expert Systems with Applications, 2024) — scores subjective answers with three independent NLP modules (keyword matching, semantic similarity, and named-entity overlap) and fuses them with a four-layer deep neural network, reporting a low regression error. That design buys accuracy at the cost of accountability: the final combiner is opaque, the grade carries no trace back to the evidence, and the paper itself lists explainability and the integration of large language models as open work. This project keeps the three modules but replaces the decision component. A symbolic pathway (spaCy, YAKE, KeyBERT, WordNet) extracts reproducible, auditable quantities; a neural pathway (an offline Sentence-BERT encoder) measures the one thing rules cannot — semantic closeness to the reference. The two are merged not by a trained network but by a Mamdani fuzzy inference system whose small, human-readable IF–THEN rule base encodes the examiner's grading policy and whose per-rule firing strengths form the justification. On the public Mohler (2011) computer-science short-answer corpus (2,273 answers, 79 questions), the fuzzy combiner beats a linear average of the same inputs (Quadratic Weighted Kappa 0.315 vs 0.209), isolating the value added by the rule base; with a single monotone (isotonic) calibration it reaches QWK 0.48, Pearson 0.61 and RMSE 18.0 on held-out data, below the mean-prediction baseline (21.9). The grader is highly stable: light paraphrasing moves a grade by only 0.24 points on average, and appending irrelevant filler does not raise the grade. The contribution is architectural: ranking comparable to a trained black box, with an auditable, editable, hallucination-free decision procedure."));
add(P([["Keywords: ", { bold: true }], "Neuro-Symbolic AI, Automated Essay Scoring, Fuzzy Inference System, Explainable AI, Sentence Embeddings, Rule-Based NLP."]));
add(new Paragraph({ children: [new PageBreak()] }));

// ===== TOC =====
add(H1("Table of Contents"));
add(new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }));
add(note("In Word: right-click the field above → Update Field → Update entire table to populate page numbers. Also insert a List of Figures and a List of Tables if required."));
add(new Paragraph({ children: [new PageBreak()] }));

// ===== 1. INTRODUCTION =====
add(H1("1. Introduction"));
add(H2("1.1 Background and Motivation"));
add(P("Written assessment is the most informative and the most expensive form of evaluation in education. A short-answer or essay question reveals whether a student can organise an argument, apply a concept and express it precisely — things a multiple-choice item cannot probe. The cost is human time, and hand grading is inconsistent: the same script graded twice frequently receives different marks. Automating subjective-answer grading has therefore been an active goal for decades, and recent systems make it appear easy."));
add(P("The parent work this project extends, Agrawal et al. [1], is representative of the current state of the art. It decomposes grading into three NLP modules — a keyword module (YAKE and KeyBERT with WordNet expansion), a semantic similarity module (Sentence-BERT and SimCSE), and a named-entity recognition module (spaCy, NLTK and CamemBERT) — and feeds their three scores into a four-layer deep neural network that regresses the final mark, reaching a very low RMSE on a self-collected computer-science dataset. Notably, the faculty for this course, Dr. Ilanthenral Kandasamy, is a co-author of that paper, making it the natural anchor for a Track-E extension."));
add(P("A low error figure, however, is not the only property an assessment instrument must have. An opaque grader is unsuitable for an institutional workflow because: (i) the mark has no trace back to the evidence, so a contested grade cannot be defended; (ii) any natural-language justification is generated after and independently of the number, so it may be fabricated (hallucination is a systemic property of generative models [4]); and (iii) automated scorers historically over-weight superficial cues such as length [3]. Rudin [6] argues that for high-stakes decisions one should build models that are interpretable by construction rather than explain a black box after the fact. Grading is such a decision."));
add(H2("1.2 Problem Statement"));
add(P([["Given a student's answer, a reference answer, and grading criteria, produce a final mark together with a complete, faithful and machine-verifiable justification, such that no single component — least of all a neural network — can unilaterally determine the mark.", { italics: true }]]));
add(H2("1.3 Research Questions"));
add(bullet("RQ1: Can the opaque DNN combiner of the three-module grader [1] be replaced by a transparent fuzzy rule base without losing ranking agreement with human examiners, while making the decision auditable?"));
add(bullet("RQ2: Does fuzzy fusion of the three module scores outperform each individual module and a simple linear average on human agreement (Quadratic Weighted Kappa)?"));
add(bullet("RQ3: Is the resulting grader stable under paraphrase and resistant to length-based gaming (padding)?"));
add(H2("1.4 Contributions"));
add(bullet([["C1 — ", { bold: true }], "We replace the parent paper's four-layer DNN combiner with a self-contained Mamdani fuzzy inference system that exposes the firing strength of every rule, so the explanation is a transcript of the computation (evidenced in §7.1, §7.4)."]));
add(bullet([["C2 — ", { bold: true }], "We re-implement all three parent modules fully offline (no external API), keeping them as auditable evidence producers (§5.3, ablation in §7.3)."]));
add(bullet([["C3 — ", { bold: true }], "We show empirically that fuzzy fusion achieves the best human agreement (QWK) of any configuration, beating every single module and a linear average on a public benchmark (§7.1, §7.3)."]));
add(bullet([["C4 — ", { bold: true }], "We evaluate robustness (paraphrase stability and padding resistance) — properties the parent paper did not measure (§7.1)."]));
add(bullet([["C5 — ", { bold: true }], "We deliver an interactive, explainable scorecard with an editable grading policy (strict/lenient) requiring no retraining (§4.5, §5.8)."]));
add(H2("1.5 Organisation of the Report"));
add(P("Section 2 reviews related work and states the research gap. Section 3 lists measurable objectives. Section 4 describes the innovation and system design. Section 5 covers data, models and implementation. Section 6 defines the evaluation protocol, and Section 7 reports and discusses results. Sections 8–10 address responsible AI, conclusions and reproducibility, followed by references and the generative-AI declaration."));

// ===== 2. LITERATURE REVIEW =====
add(H1("2. Literature Review"));
add(H2("2.1 Search Strategy"));
add(P("We searched Google Scholar, Semantic Scholar, IEEE Xplore, the ACL Anthology and arXiv using combinations of the terms automated essay scoring, short-answer grading, neuro-symbolic, fuzzy inference, explainable grading, sentence embeddings and hallucination. We prioritised peer-reviewed venues (ACL, EMNLP, IJCAI, Nature Machine Intelligence, Expert Systems with Applications, Artificial Intelligence Review, ACM Computing Surveys) and the parent paper's own reference set. Inclusion criteria: direct relevance to subjective-answer grading, neuro-symbolic/fuzzy fusion, or the specific tooling we reuse. Every cited work was opened and read; no reference was included on the basis of a chatbot recommendation alone."));
add(note("ACADEMIC-INTEGRITY NOTE: the table below lists references the author has verified. The course requires at least 12 peer-reviewed sources from 2023 onward, most from 2024–2026, each with a DOI/arXiv ID. The author must add and personally verify the additional recent sources before submission — these have been intentionally NOT auto-generated, because invented or unverified references are treated as misconduct."));
add(H2("2.2 Literature Summary Table"));
add(caption("Table 2.1: Summary of reviewed literature (add verified 2023+ rows to reach the minimum of 12)."));
add(table(
  ["#", "Authors, Year [Ref.]", "Concept / Framework", "Method & Evaluation", "Key Findings (numbers)", "Relevance to Our Project"],
  [
    ["1", "Agrawal et al., 2024 [1]", "Three-module NLP grader + DNN fusion (PARENT PAPER)", "YAKE/KeyBERT + SBERT/SimCSE + CamemBERT NER → 4-layer DNN; RMSE on ~190 CS Q&A", "RMSE ≈ 0.033–0.039 (normalised); CamemBERT best for NER", "The system we extend; we reuse its 3 modules and replace the DNN with a fuzzy rule base"],
    ["2", "Mohler, Bunescu & Mihalcea, 2011 [2]", "Short-answer grading via similarity + dependency alignment", "Semantic similarity + graph alignment; Pearson/RMSE on UNT CS corpus", "Pearson ≈ 0.46–0.52 (unsupervised)", "Source of our benchmark dataset (2,273 CS answers)"],
    ["3", "Garcez & Lamb, 2023 [3]", "Neuro-symbolic AI survey (‘3rd wave’)", "Survey / taxonomy of neural–symbolic integration", "Identifies explainability & trust as central motivations", "Frames our neural-perception / symbolic-control design"],
    ["4", "Ji et al., 2023 [4]", "Survey of hallucination in NLG", "Taxonomy + causes + mitigations", "Hallucination is systemic across NLG tasks", "Motivates removing the LLM from the decision path"],
    ["5", "Mizumoto & Eguchi, 2023 [5]", "LLM for automated essay scoring", "GPT-based zero-shot scoring of TOEFL essays; agreement with raters", "Usable agreement; improves with linguistic features", "Evidence that hybrid (features + neural) beats pure neural"],
    ["6", "Rudin, 2019 [6]", "Interpretable models for high-stakes decisions", "Position paper", "Argues against post-hoc explanation of black boxes", "Core justification for an interpretable-by-construction grader"],
    ["7", "Reimers & Gurevych, 2019 [7]", "Sentence-BERT embeddings", "Siamese BERT; STS benchmarks", "Fast, accurate sentence similarity", "Our offline neural (semantic) module"],
    ["8", "Ke & Ng, 2019 [8]", "AES state-of-the-art survey", "Survey", "Documents length bias & gaming of AES", "Motivates our padding-resistance test"],
    ["9", "Mamdani & Assilian, 1975 [9]", "Fuzzy inference controller", "Mamdani inference + defuzzification", "Linguistic control with IF-THEN rules", "Our fusion mechanism"],
    ["10", "Zadeh, 1965 [10]", "Fuzzy sets", "Membership functions μ:X→[0,1]", "Foundation of partial membership", "Basis of our linguistic variables"],
    ["11", "[ADD verified 2023+ source]", "", "", "", ""],
    ["12", "[ADD verified 2023+ source]", "", "", "", ""],
  ],
  [500, 1600, 1700, 1700, 1700, 1826], { fontSize: 17 }));
add(H2("2.3 Synthesis and Research Gap"));
add(P("Three themes emerge. (i) Feature-based AES is transparent but semantically blind and gameable by length [3], [8]. (ii) Neural and LLM-based AES is semantically capable but unaccountable, and its self-generated explanations are unreliable [4], [6]. (iii) Hybrid designs such as the parent paper [1] and [5] improve accuracy by combining linguistic and neural signals, but still fuse them inside a trained statistical model, leaving the decision itself opaque. Neuro-symbolic work [3] argues the correct remedy is to let a symbolic procedure own the decision while neural components act as bounded sensors."));
add(P([["Gap: ", { bold: true }], "no existing subjective-answer grader keeps the accuracy of multi-signal neural fusion while making the final decision auditable, editable by a non-programmer, and provably hallucination-free. This project targets exactly that gap by replacing the parent paper's DNN combiner with a transparent fuzzy rule base."]));

// ===== 3. OBJECTIVES =====
add(H1("3. Objectives of the Project"));
add(P("The project builds an explainable neuro-symbolic grader that extends a three-module NLP grader by replacing its opaque neural combiner with a fuzzy rule base, and evaluates it on a public computer-science short-answer benchmark against purely neural and purely symbolic baselines."));
add(caption("Table 3.1: Project objectives and how they are measured."));
add(table(
  ["#", "Objective (specific and measurable)", "Measured by (metric / evidence)", "Target / success criterion", "Reported in"],
  [
    ["O1", "Replace the DNN combiner with a transparent fuzzy rule base that justifies each grade", "Per-rule firing-strength trace present in every scorecard", "Every grade traceable to fired rules", "§4.5, §7.4"],
    ["O2", "Match or exceed single-module & linear-fusion ranking agreement with humans", "Quadratic Weighted Kappa on Mohler test set", "QWK(full) ≥ QWK(best module) and ≥ QWK(linear mean)", "§7.1, §7.3"],
    ["O3", "Achieve competitive regression error vs the trained parent approach", "RMSE on held-out set (after transparent calibration)", "RMSE below the mean-prediction baseline", "§7.1"],
    ["O4", "Demonstrate stability & gaming-resistance", "Paraphrase grade drift; grade change under padding", "Mean drift < 3 pts; padding does not raise grade", "§7.1"],
  ],
  [500, 2550, 2450, 2300, 1226], { fontSize: 18 }));

// ===== 4. INNOVATION & SYSTEM DESIGN =====
add(H1("4. Innovation Component and System Design"));
add(H2("4.1 Innovation Component"));
add(P("The innovation is the relocation of the grading decision from a trained black box to a transparent fuzzy rule base, without discarding the neural semantic signal. In the parent paper the three module scores enter a four-layer network whose weights are uninterpretable; a wrong or adversarial module score can silently move the mark, and the only ‘explanation’ available is a post-hoc narrative. We instead feed the same three scores into a Mamdani fuzzy inference system whose IF–THEN rules are written in natural language, can be read and edited by the examiner, and expose the firing strength of every rule. This is non-trivial: it requires (i) re-implementing the three modules so their outputs are commensurable and calibrated to a common 0–100 scale; (ii) designing membership functions and a rule base that encode a defensible grading policy; and (iii) engineering the inference engine so the per-rule trace — the justification — is recoverable, which off-the-shelf toolkits do not expose cleanly."));
add(H2("4.2 Positioning Against the Closest Existing Work"));
add(caption("Table 4.1: Comparison with the closest existing works."));
add(table(
  ["Feature / capability", "Agrawal et al. 2024 [1]", "LLM-as-grader [5]", "Mohler 2011 [2]", "Our project"],
  [
    ["Semantic understanding", "Yes (SBERT/SimCSE)", "Yes (LLM)", "Partial (similarity)", "Yes (SBERT, offline)"],
    ["Final decision mechanism", "4-layer DNN (opaque)", "LLM (opaque)", "Regression on similarity", "Fuzzy rule base (transparent)"],
    ["Per-decision justification", "No", "Post-hoc, may hallucinate", "No", "Yes (fired rules + strengths)"],
    ["Editable by non-programmer", "No", "Prompt only", "No", "Yes (swap rule set)"],
    ["Needs training on grades", "Yes", "No", "Partial", "No (rules fixed)"],
    ["Stability / gaming tested", "No", "No", "No", "Yes (paraphrase, padding)"],
    ["Runs fully offline", "Partly", "No (API)", "Yes", "Yes"],
  ],
  [2126, 1800, 1700, 1600, 1800], { fontSize: 18 }));
add(H2("4.3 System Architecture"));
add(P("Figure 4.1 shows the architecture. The input is a (student answer, reference answer) pair. Two pathways run independently and never influence one another: a symbolic pathway produces keyword, NER and mechanics scores; a neural pathway produces a semantic-similarity score (via a cross-encoder). The two informative scores — keyword coverage and semantic similarity — are the inputs to the Mamdani fuzzy engine, which owns the decision and emits a grade plus an explainable scorecard. NER is computed and reported as evidence but excluded from the decision (near-random on this corpus); mechanics enters only as a small, transparent penalty."));
add(...figure("fig_architecture.png", 560, 402, "Fig. 4.1: System architecture. The three NLP modules feed a Mamdani fuzzy engine that replaces the parent paper's DNN. The pathways meet only inside the explicit, human-readable rule base."));
add(H2("4.4 Module Description"));
add(caption("Table 4.2: Modules — purpose, inputs, outputs, technique, owner."));
add(table(
  ["Module", "Purpose", "Input → Output", "Technique", "Owner"],
  [
    ["Keyword (symbolic)", "Rubric keyword coverage", "answers → 0–100", "YAKE + KeyBERT extraction, WordNet synonym expansion, coverage %", "Sahil Barnwal"],
    ["Similarity (neural)", "Semantic closeness to reference", "answers → 0–100", "Cross-encoder (stsb-roberta-base) pair score blended with SBERT per-sentence coverage", "Sahil Barnwal"],
    ["NER (symbolic)", "Named-entity / value overlap", "answers → 0–100", "spaCy entities + numbers/big-O; Jaccard overlap", "Sahil Barnwal"],
    ["Mechanics (symbolic, advisory)", "Surface quality", "answer → 0–100", "Length adequacy, grammar-error rate, dependency depth", "Sahil Barnwal"],
    ["Fuzzy engine", "Fuse + decide + justify", "3 scores → grade + trace", "Mamdani FIS (triangular/trapezoidal MFs, min/max, centroid)", "Sahil Barnwal"],
  ],
  [1700, 1700, 1500, 2826, 1300], { fontSize: 18 }));
add(H2("4.5 AI Techniques Used and Design Rationale"));
add(H3("Task formulation"));
add(P("The AI component decides a numeric grade (0–100) for a student answer given a reference answer. Its inputs are the two texts; its output is a grade plus a scorecard. Level of autonomy: it suggests to a human examiner (decision support) — it is explicitly a research prototype, not a replacement for a human grader (see §8). Uncertainty enters through the neural similarity estimate and through keyword/entity extraction noise; the fuzzy layer bounds the effect of any single noisy input because the grade is a centroid over a small rule base rather than a product of trained weights."));
add(H3("Techniques used"));
add(caption("Table 4.3: AI techniques used (Level: a = off-the-shelf, b = configured/tuned, c = modified/implemented by us)."));
add(table(
  ["AI technique", "Used? (Y/N)", "Level", "Where in our system, and why over the alternative"],
  [
    ["Embeddings & semantic similarity (cross-encoder, sentence encoders)", "Y", "b", "Similarity module: a cross-encoder scores the pair directly (better pairwise STS than a bi-encoder), blended with SBERT sentence coverage; chosen over BM25/TF-IDF for semantic matching"],
    ["Fuzzy logic (membership functions, rule inference)", "Y", "c", "The fusion/decision layer. Mamdani chosen over Sugeno for readable, linguistic consequents the examiner can edit"],
    ["Neuro-symbolic integration (neural + symbolic, symbolic justification)", "Y", "c", "Whole architecture: neural sensor + symbolic decision; justification is the rule trace"],
    ["Uncertainty / calibration", "Y", "c", "Affine calibration of the fuzzy output (§7); QWK/Pearson reported with it"],
    ["LLM evaluation methodology (agreement metrics, human kappa)", "Y", "b", "Evaluation: QWK/Pearson/RMSE vs human grades"],
    ["Classical ML / feature engineering", "Y", "b", "Keyword/NER/mechanics features normalised to 0–100"],
    ["Large language models (generative)", "N", "—", "Deliberately excluded so nothing can hallucinate the grade"],
    ["Prompt engineering / RAG / agents / fine-tuning", "N", "—", "Not used; no generation in the pipeline"],
  ],
  [2600, 1100, 900, 4426], { fontSize: 17 }));
add(H3("Technique explanations"));
add(P([["Semantic similarity (cross-encoder). ", { bold: true }], "A cross-encoder jointly encodes the (student, reference) pair and outputs a similarity score; because attention spans both texts at once it is far more accurate on pairwise matching than a bi-encoder, which encodes each text independently. We blend it with Sentence-BERT per-sentence coverage. We use semantic matching rather than lexical overlap because two correct answers can share meaning with few shared words. Known limitation: embeddings can rate fluent-but-wrong text as similar, which is why similarity is one input to the rule base, not the decision."]));
add(P([["Fuzzy inference (Mamdani). ", { bold: true }], "Each crisp input is mapped by membership functions to degrees of Low/Medium/High (Fig. 7.1). A rule base of IF–THEN statements fires; under Mamdani, a rule's firing strength is the minimum of its antecedent memberships (fuzzy AND), it clips its consequent set, clipped sets are aggregated by maximum, and the crisp grade is the centroid of the aggregate, y* = ∫yμ(y)dy / ∫μ(y)dy. We chose Mamdani over Sugeno because Mamdani consequents are linguistic sets (Poor/Average/Good/Excellent) that an examiner can read and edit, which matters more here than Sugeno's numerical efficiency. The membership-function shapes are trapezoidal at the extremes and triangular in the middle so that the ends saturate; parameters were set from the grading policy and checked by sensitivity analysis (§7)."]));
add(P([["Neuro-symbolic integration. ", { bold: true }], "The neural encoder is a bounded sensor; the symbolic rule base owns the decision. A fabricated or wrong module value cannot unilaterally move the mark because the grade is computed by explicit rules reading all inputs — the property that distinguishes this from a prompt-only ‘symbolic’ claim."]));

// ===== 5. METHODOLOGY =====
add(H1("5. Methodology and Implementation"));
add(H2("5.1 Data"));
add(caption("Table 5.1: Dataset description."));
add(table(
  ["Attribute", "Details"],
  [
    ["Name and source", "Mohler (2011) UNT Computer Science Short Answer dataset [2] (ShortAnswerGrading v2.0)"],
    ["Licence and terms", "Publicly released for research by the University of North Texas (Mihalcea & Mohler); cite [2]"],
    ["Size", "2,273 student answers; 79 questions; one instructor reference answer per question"],
    ["Collection method", "Public benchmark; real student answers from an introductory CS course, anonymised by the dataset authors"],
    ["Grades", "Average of two human annotators, 0–5 scale (mean 4.18); rescaled to 0–100 (mean 83.7)"],
    ["Train/val/test split", "Core grader is training-free (fixed rules) → primary metrics on full set; for calibration, a seeded 80/20 split (test n=455)"],
    ["Class balance", "Strongly skewed to high grades (mean 4.18/5) — noted as a limitation for RMSE"],
    ["Personal/sensitive data", "None; answers are anonymised, no student identifiers"],
  ],
  [2600, 6426], { fontSize: 19 }));
add(H2("5.2 Preprocessing"));
add(P("Text is lowercased, contractions expanded, and punctuation/whitespace normalised (mirroring the parent paper's preprocessing). Normalisation is deterministic and leaves text human-readable. No augmentation or de-duplication is applied; because the grader is training-free there is no train/test leakage risk for the core system, and the calibration split is seeded and fixed before fitting."));
add(H2("5.3 Models Used"));
add(caption("Table 5.2: Model inventory."));
add(table(
  ["Model", "Exact version", "Open/closed", "Size", "Role", "Access"],
  [
    ["Cross-encoder", "stsb-roberta-base", "Open", "≈125M", "Semantic pair score (neural pathway)", "Local, offline"],
    ["Sentence-BERT", "all-MiniLM-L6-v2", "Open", "≈22M", "Sentence coverage (neural pathway)", "Local, offline"],
    ["spaCy", "en_core_web_sm 3.8", "Open", "—", "Tokenisation, POS, NER", "Local, offline"],
    ["KeyBERT + YAKE", "keybert 0.8 / yake 0.4", "Open", "—", "Keyword extraction", "Local, offline"],
    ["WordNet (NLTK)", "wordnet 3.1", "Open", "—", "Synonym expansion", "Local, offline"],
  ],
  [1700, 2100, 1300, 900, 2126, 900], { fontSize: 18 }));
add(P("No hosted/closed models and no API calls are used; all experiments ran on CPU in October 2026."));
add(H2("5.4 Prompting, Fine-tuning and Retrieval Configuration"));
add(P("Not applicable. The system uses no generative model, no prompting, no fine-tuning and no retrieval index. The ‘configuration’ that governs behaviour is the fuzzy membership functions and rule base (§4.5, §5.5), which are declarative and stored in the repository's config module."));
add(H2("5.5 Experimental Setup and Hyperparameters"));
add(caption("Table 5.3: Settings and fuzzy parameters."));
add(table(
  ["Parameter", "Value(s)", "How chosen"],
  [
    ["Input membership functions (0–100)", "Low = trap(0,0,20,45); Medium = tri(30,50,70); High = trap(55,80,100,100)", "From grading policy; sensitivity-checked (§7.3)"],
    ["Output MFs (grade, 5 sets)", "Poor trap(0,0,12,28); Average tri(20,38,55); Good tri(48,62,76); VeryGood tri(70,82,92); Excellent trap(85,94,100,100)", "Upper sets placed high to reduce range compression"],
    ["Fuzzy decision inputs", "keyword, similarity (NER excluded — near-random)", "Lever 1: drop a weak sensor"],
    ["Inference / defuzzification", "Mamdani (min/max) / centroid", "Readable linguistic consequents"],
    ["Rule base size", "strict = 9 rules; lenient = 6 rules", "Hand-authored from examiner policy"],
    ["Similarity", "cross-encoder stsb-roberta-base (0.7) + SBERT coverage (0.3)", "Lever 2: cross-encoder for pairwise STS"],
    ["Mechanics penalty weight", "0.10", "Advisory only; never dominant"],
    ["Calibration", "isotonic (monotone) fit on 80% train; selected over affine", "Lever 4: reduces RMSE, raises QWK"],
    ["Seeds / runs", "Deterministic (seed 42 for split, seed 7 for robustness sample)", "Reproducibility"],
  ],
  [2400, 4426, 2200], { fontSize: 18 }));
add(H2("5.6 Compute and Cost"));
add(caption("Table 5.4: Compute and cost."));
add(table(
  ["Item", "Details"],
  [
    ["Hardware", "Commodity CPU laptop (no GPU required), ≈4 GB RAM"],
    ["Training / indexing time", "None (training-free); one-time model download only"],
    ["Inference latency", "≈14 ms per answer (mean) with module caching; full 2,273-answer benchmark in ≈30 s"],
    ["API tokens / cost", "₹0 / $0 — fully offline, no API"],
  ],
  [2600, 6426], { fontSize: 19 }));
add(H2("5.7 Tools and Frameworks"));
add(caption("Table 5.5: Tools used and justification."));
add(table(
  ["Tool / library", "Version", "Purpose", "Why chosen"],
  [
    ["Python", "3.12", "Implementation", "Ecosystem for NLP"],
    ["sentence-transformers", "2.x", "SBERT embeddings", "Standard, offline, fast"],
    ["spaCy", "3.8", "Parsing, NER", "Robust English pipeline"],
    ["YAKE / KeyBERT", "0.4 / 0.8", "Keyword extraction", "Matches parent paper"],
    ["NumPy / SciPy", "latest", "Fuzzy engine, metrics", "Custom Mamdani with rule trace"],
    ["Streamlit", "1.x", "Demo UI", "Fast interactive scorecard"],
    ["matplotlib", "3.x", "Figures / membership plots", "Publication-quality plots"],
  ],
  [2100, 1300, 2800, 2826], { fontSize: 18 }));
add(H2("5.8 Implementation, Screenshots and Demo"));
add(P([["GitHub repository (mandatory): ", { bold: true }], [" [INSERT REPOSITORY URL]", { bold: true, color: "B00000" }], ["     Demo video (mandatory): ", { bold: true }], [" [INSERT 3–5 MIN VIDEO URL]", { bold: true, color: "B00000" }]]));
add(P("The repository contains the full pipeline (src/), the Streamlit app (app/), evaluation scripts (eval/), unit tests (tests/), and a README with a one-command reproduction of the main results table (python -m eval.benchmark). A worked scorecard produced by the live system is shown in Fig. 7.2."));

// ===== 6. EVALUATION PROTOCOL =====
add(H1("6. Evaluation Protocol"));
add(H2("6.1 Evaluation Data and Split Hygiene"));
add(P("Evaluation uses the full Mohler corpus (2,273 answers). The core grader has no trained parameters, so it is evaluated on the entire set without leakage. For the optional calibration only, we fix a seeded 80/20 split before fitting and report calibration metrics on the untouched 20% test partition (n=455). Robustness uses a separate seeded random sample of 400 answers."));
add(H2("6.2 Metrics"));
add(bullet([["Quadratic Weighted Kappa (QWK): ", { bold: true }], "agreement between system and human grades on ordinal bins, penalising larger disagreements quadratically; the standard AES metric and the Track-E recommended agreement measure for grading."]));
add(bullet([["Pearson correlation r: ", { bold: true }], "linear agreement with human grades; invariant to affine rescaling, so it isolates ranking quality from calibration."]));
add(bullet([["RMSE: ", { bold: true }], "root-mean-square error on the 0–100 scale; comparable in spirit to the parent paper's regression error."]));
add(bullet([["Robustness: ", { bold: true }], "mean absolute grade drift under paraphrase; mean grade change under padding."]));
add(H2("6.3 Baselines"));
add(P("Following Track E (purely neural vs purely symbolic vs hybrid), we compare against: (i) a naive mean-baseline (predict the mean human grade); (ii) a purely neural baseline — the SBERT similarity module alone; (iii) purely symbolic baselines — keyword-only and NER-only; and (iv) the strong baseline — a linear average of the same two inputs the fuzzy system uses, which isolates the contribution of the rule base from the choice of inputs."));
add(H2("6.4 Human Evaluation and LLM-as-a-Judge"));
add(P("No LLM-as-a-judge is used. Ground-truth grades are the Mohler dataset's human annotations (two annotators per answer, averaged), so all agreement metrics are computed against real human judgement."));
add(H2("6.5 Statistical Analysis"));
add(P("The grader is deterministic (no sampling), so repeated runs give identical scores; variance is not from stochastic inference but from the data. We report metrics over the full corpus and, for calibration, on a held-out split. Robustness is summarised by mean and maximum drift over 400 samples. Suggested extension (noted in §7.6): paired bootstrap 95% confidence intervals on the QWK difference between the fuzzy system and the linear baseline."));

// ===== 7. RESULTS =====
add(H1("7. Results and Discussion"));
add(H2("7.1 Main Results"));
add(caption("Table 7.1: Main results on the Mohler corpus (2,273 answers, full set). Best QWK in bold."));
add(table(
  ["Method", "RMSE (0–100)", "Pearson r", "QWK"],
  [
    ["mean-baseline (naive)", "21.93", "0.000", "0.000"],
    ["keyword-only (symbolic)", "51.91", "0.469", "0.177"],
    ["similarity-only (neural, cross-encoder)", "36.33", "0.554", "0.248"],
    ["ner-only (symbolic)", "42.45", "0.068", "0.063"],
    ["mean-of-modules (linear, 3 modules)", "33.83", "0.446", "0.251"],
    ["mean(keyword+similarity) (linear, same inputs)", "42.83", "0.539", "0.209"],
    ["full-fuzzy (strict policy)", "42.35", "0.552", "0.244"],
    ["full-fuzzy (lenient), uncalibrated — OURS", "35.33", "0.551", "0.315"],
    ["full-fuzzy (lenient) + calibration — OURS", "17.65", "0.594", "0.459"],
  ],
  [3600, 1842, 1792, 1792], { fontSize: 18 }));
add(P("The lenient fuzzy combiner attains the highest QWK of any uncalibrated configuration (0.315), and — the decisive comparison — beats a linear average of the SAME two inputs (0.209). This answers RQ2 and isolates the rule base's contribution: with identical inputs, fuzzy fusion raises QWK by more than 0.10 over a plain average. The cross-encoder lifts the semantic module's Pearson to 0.55, which the full system inherits. NER is excluded from the decision (near-random here, r=0.07) but still reported as evidence."));
add(P([["Calibration. ", { bold: true }], "Centroid defuzzification compresses the output range, so raw grades sit below a corpus whose human mean is 83.7; RMSE therefore favours the constant mean-baseline. We select between an affine and an isotonic map on an 80% train split and evaluate on the held-out 20% (isotonic chosen). This monotone rescaling reduces test RMSE from 33.9 to 17.99 — below the mean-baseline (21.93) — and raises test QWK from 0.355 to 0.481 and Pearson from 0.58 to 0.612. This answers RQ3's accuracy aspect: competitive error with a transparent one-step rescaling, no network training."]));
add(caption("Table 7.2: Robustness (random sample of 400 answers)."));
add(table(
  ["Test", "Result", "Interpretation"],
  [
    ["Paraphrase: mean abs. grade drift", "0.24 pts", "Very stable under synonym substitution"],
    ["Padding: mean grade change", "−0.51 pts", "Filler does not raise grades — resists length-gaming"],
  ],
  [3400, 2000, 3626], { fontSize: 19 }));
add(H2("7.2 Comparative Analysis"));
add(P("Against the parent paper [1], which reports a very low trained-DNN RMSE on its own ~190-answer corpus, our training-free system is not directly comparable on RMSE (different data; no fitting to grades). The fair comparison is within our corpus: our fuzzy combiner beats both the neural-only and symbolic-only baselines on QWK, and beats linear fusion of the identical signals. Against unsupervised Mohler baselines [2] (Pearson ≈ 0.46–0.52), our Pearson of 0.48 is in range while additionally providing a full justification and stability guarantees that [1], [2] do not offer."));
add(H2("7.3 Ablation Study"));
add(caption("Table 7.3: Ablation — effect of each component (QWK, full set)."));
add(table(
  ["Configuration", "QWK", "Change vs full system"],
  [
    ["Full system (lenient fuzzy, uncalibrated)", "0.315", "—"],
    ["− fuzzy layer (linear mean of same 2 inputs)", "0.209", "−0.106"],
    ["similarity module only (neural)", "0.248", "−0.067"],
    ["keyword module only (symbolic)", "0.177", "−0.138"],
    ["strict instead of lenient policy", "0.244", "−0.071 (policy mismatch)"],
    ["+ calibration (shipped system)", "0.459", "+0.144"],
  ],
  [4200, 1600, 3226], { fontSize: 18 }));
add(P("Replacing the fuzzy layer with a linear average of the SAME two inputs drops QWK from 0.315 to 0.209 — the clearest evidence that the rule base, not merely the choice of inputs, drives the agreement gain (+0.106). Policy choice matters (a mismatched strict policy costs 0.071 QWK), and the final calibration adds a further +0.144. A sensitivity check widening/narrowing the Medium membership function by ±10 points changed QWK by < 0.02, so the result is not an artefact of a single arbitrary parameter."));
add(H2("7.4 Error Analysis"));
add(P("Representative failure modes (full traces in the repository):"));
add(bullet("(1) Correct paraphrase, low NER: an answer semantically correct but lacking the reference's named entities scores NER = 0; the fuzzy layer absorbs it (grade stays high) — a success of symbolic control, but it means NER is near-uninformative on this corpus (r = 0.07)."));
add(bullet("(2) Keyword stuffing: an answer listing reference terms without connective meaning gets high keyword but low similarity; the ‘terms-without-understanding → Average’ rule correctly caps it."));
add(bullet("(3) Very short correct answer: length-adequacy lowers mechanics, applying a small penalty that occasionally under-grades terse-but-correct answers."));
add(bullet("(4) Range compression: genuinely excellent answers rarely exceed ~85 before calibration, the main driver of uncalibrated RMSE."));
add(bullet("(5) Over-generous floor: after isotonic calibration the very worst answers (human 0) still receive ~60, because the corpus has few low examples to anchor the low end — the main remaining error, visible in the scatter (Fig. B.1)."));
add(H2("7.5 Answers to the Research Questions"));
add(P([["RQ1 — ", { bold: true }], "Yes: the DNN is replaced by a fuzzy rule base that preserves ranking (competitive Pearson/QWK) while making every grade traceable to the rules that produced it (Fig. 7.2)."]));
add(P([["RQ2 — ", { bold: true }], "Yes: the fuzzy combiner's QWK (0.315) exceeds every single module and a linear average of the same two inputs (0.209)."]));
add(P([["RQ3 — ", { bold: true }], "Yes: mean paraphrase drift is 0.24 pts and padding changes grades by −0.51 pts (does not reward verbosity)."]));
add(H2("7.6 Threats to Validity and Limitations"));
add(P("Internal validity: range compression necessitates calibration for absolute scores; we report both uncalibrated and calibrated numbers to avoid overstating. External validity: evaluation is on one CS short-answer corpus; longer essays and other subjects remain untested. Construct validity: QWK/Pearson measure agreement with two annotators whose own agreement bounds achievable scores, and the corpus skew makes RMSE a weak discriminator — hence rank metrics are primary. A paired bootstrap CI on the fuzzy-vs-linear QWK gap would further strengthen the claim."));
add(...figure("fig_membership.png", 560, 213, "Fig. 7.1: Input membership functions (left) and output grade membership functions (right)."));
add(...figure("fig_scorecard.png", 540, 344, "Fig. 7.2: A worked scorecard. Keyword 70, similarity 85, NER 0 → the ‘similarity High AND keyword High → Excellent’ rule fires (strength 0.60); centroid grade 86/100 (A). The explanation is the computation."));
add(...figure("fig_ablation.png", 560, 277, "Fig. 7.3: Ablation — the lenient fuzzy combiner has the highest QWK; NER alone is near-random yet does not drag down the combiner."));

// ===== 8. RESPONSIBLE AI =====
add(H1("8. Responsible AI and Ethical Considerations"));
add(P([["This is a high-stakes domain (exam/assessment). ", { bold: true }], "The system is a research prototype and decision-support aid for an examiner; it is not a replacement for a human grader and no student's final mark should be set by it unreviewed."]));
add(H2("8.1 Risk Assessment"));
add(caption("Table 8.1: Risks and mitigations."));
add(table(
  ["Risk", "Who could be harmed", "Likelihood / severity", "Mitigation implemented"],
  [
    ["Unfair/incorrect grade from an opaque model", "Students", "Med / high", "Transparent fuzzy rules + per-grade scorecard; examiner can audit and override"],
    ["Over-reliance / automation bias", "Students, institution", "Med / high", "Positioned as decision support; mechanics advisory only; human-in-the-loop"],
    ["Gaming via verbosity / keyword stuffing", "Honest students", "Med / med", "Padding-resistance tested; ‘terms-without-understanding’ rule"],
    ["Semantic model misjudges fluent-but-wrong text", "Students", "Med / med", "Neural score is one input of three; rule base bounds its influence"],
    ["Bias across writing styles / dialects", "Subgroups of students", "Low-Med / med", "Flagged for subgroup testing (not yet measured) in future work"],
  ],
  [2300, 1700, 1600, 3426], { fontSize: 18 }));
add(H2("8.2 Data Privacy and Consent"));
add(P("The Mohler corpus is a public, anonymised research dataset with no student identifiers; no personal or sensitive data is processed. No new human data was collected, so no additional consent is required. The design is compatible with the Digital Personal Data Protection Act, 2023, as it stores no personal data."));
add(H2("8.3 Fairness"));
add(P("The system could in principle grade differently across writing styles, first-language backgrounds or dialects via the semantic model's training bias. This was not measured on subgroups (the corpus lacks demographic labels) and is listed as a limitation and future-work item; the transparent scorecard at least makes any systematic pattern inspectable, which an opaque DNN does not."));
add(H2("8.4 Safety, Security and Misuse"));
add(P("The system generates no free text (no prompt-injection or jailbreak surface) and makes no autonomous decision. The main misuse risk is deploying it as a sole grader without review; the report and README state explicitly that it is a prototype requiring human oversight."));
add(H2("8.5 Licences and Attribution"));
add(P("Reused components are open-source under permissive licences (spaCy MIT, sentence-transformers Apache-2.0, YAKE, KeyBERT MIT, NLTK/WordNet). The Mohler dataset is used under its research-release terms with citation [2]. The project repository is released under the MIT License. The parent paper [1] is credited as the design this work extends."));

// ===== 9. CONCLUSION =====
add(H1("9. Conclusion and Future Work"));
add(P("We extended the three-module NLP grader of Agrawal et al. [1] by replacing its opaque deep-network combiner with a transparent Mamdani fuzzy inference system and keeping the neural semantic component fully offline. Against the objectives: O1 is met (every grade carries its fired-rule trace); O2 is met (QWK 0.315 beats a linear average of the same inputs, 0.209); O3 is met (calibrated held-out RMSE 17.99 < baseline 21.93); O4 is met (paraphrase drift 0.24 pts, padding −0.51 pts). The main lesson: for subjective grading, moving the decision from a trained network to an editable rule base costs little in ranking agreement and buys auditability, editability and stability. Future work: paired-bootstrap significance tests; genetic tuning of membership functions while keeping rules readable; subgroup fairness testing; longer essays and other subjects; and an optional constrained-LLM sensor behind the same interface (the parent paper's stated direction) without ceding the decision to it."));

// ===== 10. REPRODUCIBILITY =====
add(H1("10. Reproducibility Checklist"));
add(table(
  ["Item", "Yes / No / NA", "Location"],
  [
    ["Repository shared with faculty; README has setup & run steps", "Yes", "[repo URL] / README.md"],
    ["Dependencies pinned", "Yes", "requirements.txt"],
    ["Exact model identifiers and experiment dates recorded", "Yes", "§5.3, §5.6"],
    ["All prompts included", "NA", "No generative model / prompts used"],
    ["Random seeds fixed and reported", "Yes", "§5.5 (seed 42 / 7)"],
    ["Evaluation set or script to regenerate it provided", "Yes", "src/datasets.py, data/"],
    ["One script reproduces the main results table", "Yes", "python -m eval.benchmark"],
    ["Data sources and licences listed", "Yes", "§5.1, §8.5"],
    ["No API keys / passwords / personal data in repo", "Yes", "Offline; no secrets"],
    ["Compute and API cost reported", "Yes", "§5.6 (₹0)"],
    ["Demo video link opens without a permission request", "[verify]", "[video URL]"],
  ],
  [4600, 1600, 2826], { fontSize: 18 }));

// ===== 11. REFERENCES =====
add(H1("11. References"));
add(note("Verify every entry against its source. The course requires ≥12 peer-reviewed references from 2023 onward (most 2024–2026); add verified recent sources at [11]–[12]+. Do not insert any reference you have not personally opened."));
const refs = [
  "[1] R. Agrawal, H. Mishra, I. Kandasamy, S. R. Terni, and W. B. Vasantha, “Revolutionizing subjective assessments: A three-pronged comprehensive approach with NLP and deep learning,” Expert Systems with Applications, vol. 239, 122470, 2024, doi: 10.1016/j.eswa.2023.122470.",
  "[2] M. Mohler, R. Bunescu, and R. Mihalcea, “Learning to grade short answer questions using semantic similarity measures and dependency graph alignments,” in Proc. 49th Annual Meeting of the ACL: Human Language Technologies, Portland, OR, USA, 2011, pp. 752–762.",
  "[3] A. d’Avila Garcez and L. C. Lamb, “Neurosymbolic AI: The 3rd wave,” Artificial Intelligence Review, vol. 56, no. 11, pp. 12387–12406, 2023, doi: 10.1007/s10462-023-10448-w.",
  "[4] Z. Ji et al., “Survey of hallucination in natural language generation,” ACM Computing Surveys, vol. 55, no. 12, pp. 1–38, 2023, doi: 10.1145/3571730.",
  "[5] A. Mizumoto and M. Eguchi, “Exploring the potential of using an AI language model for automated essay scoring,” Research Methods in Applied Linguistics, vol. 2, no. 2, 100050, 2023, doi: 10.1016/j.rmal.2023.100050.",
  "[6] C. Rudin, “Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead,” Nature Machine Intelligence, vol. 1, pp. 206–215, 2019, doi: 10.1038/s42256-019-0048-x.",
  "[7] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence embeddings using Siamese BERT-networks,” in Proc. EMNLP-IJCNLP, Hong Kong, 2019, pp. 3982–3992, doi: 10.18653/v1/D19-1410.",
  "[8] Z. Ke and V. Ng, “Automated essay scoring: A survey of the state of the art,” in Proc. 28th Int. Joint Conf. Artificial Intelligence (IJCAI), Macao, 2019, pp. 6300–6308, doi: 10.24963/ijcai.2019/879.",
  "[9] E. H. Mamdani and S. Assilian, “An experiment in linguistic synthesis with a fuzzy logic controller,” International Journal of Man-Machine Studies, vol. 7, no. 1, pp. 1–13, 1975, doi: 10.1016/S0020-7373(75)80002-2.",
  "[10] L. A. Zadeh, “Fuzzy sets,” Information and Control, vol. 8, no. 3, pp. 338–353, 1965, doi: 10.1016/S0019-9958(65)90241-X.",
  "[11] [ADD a verified peer-reviewed reference from 2023–2026 with DOI/arXiv ID].",
  "[12] [ADD a verified peer-reviewed reference from 2023–2026 with DOI/arXiv ID].",
];
refs.forEach((r) => add(new Paragraph({ spacing: { line: 300, after: 80 },
  children: [new TextRun({ text: r, font: FONT, size: 22 })] })));

// ===== 12. GEN-AI DECLARATION =====
add(H1("12. Declaration of Generative AI Use"));
add(P("This section covers AI tools used to produce the project and report. AI models that are components of the system are described in §5.3, not here."));
add(caption("Table 12.1: Generative AI tools used."));
add(table(
  ["Tool and version", "Purpose", "Files / sections affected", "Extent", "How verified"],
  [
    ["AI coding/writing assistant", "Scaffold code, draft report prose, generate figures", "src/, eval/, this report", "Substantial draft code & text", "All code executed & unit-tested (tests/); all results regenerated by the author via eval/benchmark.py; every reference checked against its source"],
  ],
  [1900, 1900, 1900, 1400, 1926], { fontSize: 18 }));
add(P("We confirm that we have reviewed, tested and understood all AI-assisted content; that every reference was checked against its original source; and that we take full responsibility for the accuracy and integrity of this report and code."));
add(note("Complete this table accurately with the specific tool(s) and version(s) you used; undisclosed use is treated as academic misconduct, and any listed file may be examined line-by-line in the viva."));

// ===== APPENDIX =====
add(new Paragraph({ children: [new PageBreak()] }));
add(H1("Appendices"));
add(H2("Appendix A — Rule Base (the grading policy)"));
add(P("Inputs: keyword coverage and semantic similarity (NER excluded from the decision). Strict policy (9 rules): (1) sim High AND kw High → Excellent; (2) sim High AND kw Medium → Very Good; (3) sim High AND kw Low → Good; (4) sim Medium AND kw High → Very Good; (5) sim Medium AND kw Medium → Good; (6) sim Medium AND kw Low → Average; (7) kw High AND sim Low → Average (terms without understanding); (8) sim Low AND kw Medium → Average; (9) sim Low AND kw Low → Poor. Lenient policy (6 rules): (1) sim High → Excellent; (2) sim Medium AND kw High → Very Good; (3) sim Medium → Good; (4) kw High AND sim Low → Average; (5) kw Medium AND sim Low → Average; (6) sim Low AND kw Low → Poor."));
add(H2("Appendix B — Additional Figures"));
add(...figure("fig_scatter.png", 360, 318, "Fig. B.1: System vs human grades (lenient) — positive correlation with a downward offset from range compression."));
add(...figure("fig_distribution.png", 380, 271, "Fig. B.2: Grade distributions — the human corpus is skewed high; the system is more central before calibration."));

// ---------- document ----------
const doc = new Document({
  creator: "Team 35 — BCSE306",
  title: "Neuro-Symbolic Automated Essay and Answer Grading with Rule-Based Justification",
  styles: {
    default: {
      document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 360 } } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 28, bold: true, color: "2E4A7A" }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true }, paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "rq", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "", alignment: AlignmentType.LEFT }] },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: ["Page ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], font: FONT, size: 18 })] })] }),
    },
    children: content,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "Team35_BCSE306_FinalReview.docx");
  fs.writeFileSync(out, buf);
  console.log("WROTE", out, buf.length, "bytes");
});
