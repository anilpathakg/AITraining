# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/6_Model_Evaluation.py
# Purpose       : Doctor/Admin Section — Model Evaluation page.
#                 Implements LLM-as-judge evaluation (equivalent
#                 to QAEvalChain) to assess accuracy, relevance,
#                 completeness, clarity, and safety of agent
#                 responses across 8 predefined test cases.
#                 Also supports ad-hoc single response scoring.
# =============================================================

import streamlit as st
import json
import time
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from evaluation.evaluator import ResponseEvaluator, EVAL_TEST_CASES
from evaluation.logger import log_evaluation

st.set_page_config(page_title="Model Evaluation", page_icon="📊", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "admin"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("📊 Model Evaluation")
st.caption("Doctor / Admin Section — LLM-as-Judge QA Evaluation")
st.divider()

tab1, tab2 = st.tabs(["🧪 Run Evaluation Suite", "📝 Single Response Eval"])

# ── Tab 1: Full evaluation suite ─────────────────────────────
with tab1:
    st.subheader("Evaluation Test Suite")
    st.info(
        f"**{len(EVAL_TEST_CASES)} test cases** across categories: "
        "Patient Lookup, Medical History RAG, Appointment Booking, "
        "Medical Information Search, Multi-step."
    )

    with st.expander("📋 View All Test Cases"):
        tc_data = [
            {"ID": tc["id"], "Category": tc["category"],
             "Query": tc["query"], "Expected Tool": tc["tool_expected"]}
            for tc in EVAL_TEST_CASES
        ]
        st.dataframe(pd.DataFrame(tc_data), width='stretch')

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_ids = st.multiselect(
            "Select test cases to run (empty = run all)",
            [tc["id"] for tc in EVAL_TEST_CASES],
            default=[]
        )
    with col2:
        st.markdown("###")
        run_btn = st.button("▶️ Run Evaluation", type="primary", width='stretch')

    if run_btn:
        with st.spinner("Initialising agent for evaluation..."):
            from agent import HealthcareAgent
            from tools.rag_tool import build_vector_store
            build_vector_store()
            eval_agent = HealthcareAgent(session_id="eval_run", enable_logging=False)
            evaluator  = ResponseEvaluator()

        cases_to_run = [
            tc for tc in EVAL_TEST_CASES
            if not selected_ids or tc["id"] in selected_ids
        ]
        progress_bar = st.progress(0)
        status_text  = st.empty()
        results_list = []

        for i, tc in enumerate(cases_to_run):
            status_text.text(f"Running {tc['id']}: {tc['query'][:50]}...")
            result = evaluator.run_test_case(eval_agent, tc)

            # Log each evaluation result for analytics dashboard
            log_evaluation(tc["query"], result.get("response_preview", ""),
                           result.get("scores", {}), session_id="eval_run")

            results_list.append(result)
            eval_agent.reset_session()
            progress_bar.progress((i + 1) / len(cases_to_run))

        status_text.text("✅ Evaluation complete!")
        st.session_state["eval_results"] = results_list

    # ── Display results ───────────────────────────────────────
    if st.session_state.get("eval_results"):
        results   = st.session_state["eval_results"]
        completed = [r for r in results if r["status"] == "completed"]

        st.divider()
        st.subheader("📈 Results Summary")

        avg_score = round(
            sum(r["scores"].get("overall", 0) for r in completed) / len(completed), 2
        ) if completed else 0
        tool_acc  = round(
            sum(1 for r in completed if r.get("tool_correct")) / len(completed) * 100, 1
        ) if completed else 0
        avg_rt    = round(
            sum(r["response_time_ms"] for r in completed) / len(completed)
        ) if completed else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tests Run",              len(results))
        m2.metric("Avg Overall Score",      f"{avg_score}/10")
        m3.metric("Tool Selection Accuracy",f"{tool_acc}%")
        m4.metric("Avg Response Time",      f"{int(avg_rt)}ms")

        # Score breakdown table
        score_data = []
        for r in completed:
            s = r["scores"]
            score_data.append({
                "Test": r["test_id"], "Category": r["category"],
                "Relevance": s.get("relevance", 0),
                "Accuracy":  s.get("accuracy", 0),
                "Completeness": s.get("completeness", 0),
                "Clarity":   s.get("clarity", 0),
                "Safety":    s.get("safety", 0),
                "Overall":   s.get("overall", 0),
                "Tool OK":   "✅" if r.get("tool_correct") else "❌",
                "Time (ms)": r["response_time_ms"]
            })

        if score_data:
            df = pd.DataFrame(score_data)
            st.dataframe(df, width='stretch')

            st.subheader("📊 Category Score Breakdown")
            cat_df = df.groupby("Category")[
                ["Relevance","Accuracy","Completeness","Clarity","Safety","Overall"]
            ].mean().round(2)
            st.bar_chart(cat_df)

        # Detailed per-test results
        st.subheader("🔍 Detailed Results")
        for r in completed:
            score  = r["scores"].get("overall", 0)
            colour = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
            with st.expander(
                f"{colour} {r['test_id']} | {r['category']} | Score: {score}/10"
            ):
                st.markdown(f"**Query:** {r['query']}")
                st.markdown(f"**Response Preview:** {r['response_preview']}")
                st.markdown(f"**Tools Used:** {', '.join(r['tools_used']) or 'None'}")
                st.markdown(
                    f"**Expected Tool:** `{r['expected_tool']}` "
                    f"{'✅' if r.get('tool_correct') else '❌'}"
                )
                sc = r["scores"]
                c1,c2,c3,c4,c5 = st.columns(5)
                c1.metric("Relevance",    f"{sc.get('relevance',0)}/10")
                c2.metric("Accuracy",     f"{sc.get('accuracy',0)}/10")
                c3.metric("Completeness", f"{sc.get('completeness',0)}/10")
                c4.metric("Clarity",      f"{sc.get('clarity',0)}/10")
                c5.metric("Safety",       f"{sc.get('safety',0)}/10")
                if sc.get("strengths"):
                    st.success(f"✅ {sc['strengths']}")
                if sc.get("improvements"):
                    st.warning(f"⚠️ {sc['improvements']}")

# ── Tab 2: Single response evaluation ─────────────────────────
with tab2:
    st.subheader("Evaluate a Single Response")
    eval_query    = st.text_area("User Query",
                                  placeholder="Enter the user's question")
    eval_response = st.text_area("Agent Response",
                                  placeholder="Paste the agent's response here",
                                  height=150)
    eval_keywords = st.text_input("Expected Keywords (comma separated)",
                                   placeholder="e.g. diabetes, treatment, insulin")

    if st.button("📊 Evaluate", type="primary"):
        if eval_query and eval_response:
            keywords = (
                [k.strip() for k in eval_keywords.split(",") if k.strip()]
                if eval_keywords else None
            )
            with st.spinner("Evaluating..."):
                evaluator  = ResponseEvaluator()
                result     = evaluator.evaluate_response(
                    query=eval_query, response=eval_response,
                    expected_keywords=keywords
                )
                log_evaluation(eval_query, eval_response, result.get("scores", {}))

            if result["status"] == "success":
                sc = result["scores"]
                st.success("Evaluation complete!")
                c1,c2,c3,c4,c5,c6 = st.columns(6)
                c1.metric("Relevance",    f"{sc.get('relevance',0)}/10")
                c2.metric("Accuracy",     f"{sc.get('accuracy',0)}/10")
                c3.metric("Completeness", f"{sc.get('completeness',0)}/10")
                c4.metric("Clarity",      f"{sc.get('clarity',0)}/10")
                c5.metric("Safety",       f"{sc.get('safety',0)}/10")
                c6.metric("Overall",      f"{sc.get('overall',0)}/10")
                if sc.get("keyword_coverage") is not None:
                    st.metric("Keyword Coverage", f"{sc['keyword_coverage']}/10")
                if sc.get("strengths"):
                    st.success(f"✅ {sc['strengths']}")
                if sc.get("improvements"):
                    st.warning(f"⚠️ {sc['improvements']}")
            else:
                st.error(f"Evaluation error: {result.get('message')}")
        else:
            st.warning("Please enter both query and response.")
