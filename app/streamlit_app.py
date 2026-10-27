"""Streamlit demo: paste a student answer + reference answer, press Grade, and
see the full neuro-symbolic scorecard -- module scores, fired fuzzy rules with
their strengths, evidence, and membership plots.

Run:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config                     # noqa: E402
from src.grader import Grader              # noqa: E402
from src.scorecard import plot_scorecard   # noqa: E402


@st.cache_resource
def get_grader(policy: str) -> Grader:
    return Grader(policy)


st.set_page_config(page_title="Neuro-Symbolic Grader", layout="wide")
st.title("Neuro-Symbolic Essay & Answer Grader")
st.caption("Three NLP modules (keyword · semantic · NER) fused by a Mamdani fuzzy "
           "rule base. The grade comes with the rules that produced it.")

with st.sidebar:
    st.header("Grading policy")
    policy = st.radio("Rule base", ["strict", "lenient"],
                      index=0 if config.GRADING_POLICY == "strict" else 1)
    st.markdown("The policy is just a swappable rule base — no code changes.")

DEFAULT_Q = "What is a stack data structure?"
DEFAULT_REF = ("A stack is a linear data structure that follows the Last In First "
               "Out (LIFO) principle, where elements are inserted and removed from "
               "the same end called the top using push and pop operations.")
DEFAULT_STU = ("A stack is a linear structure working on LIFO order. We push to add "
               "an element on top and pop to remove the top element.")

question = st.text_input("Question (optional)", DEFAULT_Q)
col1, col2 = st.columns(2)
with col1:
    reference = st.text_area("Reference answer", DEFAULT_REF, height=180)
with col2:
    student = st.text_area("Student answer", DEFAULT_STU, height=180)

if st.button("Grade", type="primary"):
    if not student.strip() or not reference.strip():
        st.warning("Please provide both a student answer and a reference answer.")
        st.stop()
    with st.spinner("Grading…"):
        grader = get_grader(policy)
        card = grader.grade(student, reference, question)

    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric("Final grade", f"{card.final_grade:.1f}/100")
    c2.metric("Letter", card.letter)
    c3.write("**Module scores**")
    c3.json({k: round(v, 1) for k, v in card.module_scores.items()})

    st.subheader("Fuzzy rules that fired — the justification")
    if card.fuzzy.fired_rules:
        st.table([
            {"firing strength": r.firing_strength, "rule": r.text,
             "→ grade set": r.consequent}
            for r in card.fuzzy.fired_rules
        ])
    else:
        st.info("No rules fired for these inputs.")

    st.subheader("Membership functions & defuzzification")
    st.pyplot(plot_scorecard(card))

    with st.expander("Full evidence (raw module output)"):
        st.json(card.to_dict())
