# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/9_AI_Governance.py
# Purpose       : Admin-only Governance & Safety dashboard.
#                 Visualises all 5 responsible AI pillars with
#                 live session data from the audit log.
#
# ══════════════════════════════════════════════════════════════
# GOVERNANCE PILLAR 3 — AUDIT LOGGING & OBSERVABILITY
# (This page is the primary UI for Pillar 3, but surfaces data
#  from all 5 pillars in one place.)
# ══════════════════════════════════════════════════════════════
#
# WHY THIS PAGE EXISTS:
#   In a production responsible AI system, administrators need
#   a single pane of glass to monitor:
#     - Did any queries get blocked? Why?
#     - How is the model performing in real time?
#     - What governance events happened this session?
#     - Is the token budget healthy?
#     - Are HITL approvals being handled promptly?
#
#   This page answers all five questions — one section per pillar.
#
# DESIGN PRINCIPLE:
#   Governance lives in the ADMIN SECTION, not on the patient-
#   facing or doctor-facing pages.  Patients and doctors use
#   the system normally.  Admins see the full governance picture
#   here.  This mirrors how real healthcare IT systems work.
#
# V4 NOTE: This entire page is NEW in V4. No equivalent existed in V3.
# ══════════════════════════════════════════════════════════════

import streamlit as st
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar

st.set_page_config(
    page_title="AI Governance & Safety",
    page_icon="🛡️",
    layout="wide"
)

# Admin-only page — force admin role in sidebar
st.session_state["role"] = "admin"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("🛡️ AI Governance & Safety Dashboard")
st.caption(
    "Real-time monitoring across all 5 Responsible AI pillars · "
    "Admin Section · V4"
)
st.divider()


# ── Load governance data ──────────────────────────────────────
# Pull from the audit log (logger.py) and cost controller
# (stored in agent session state if available).

try:
    from evaluation.logger import (
        get_governance_logs,
        get_governance_summary,
        get_analytics_summary,
        get_logs_by_type,
    )
    gov_logs    = get_governance_logs()
    gov_summary = get_governance_summary()
    ops_summary = get_analytics_summary()
except Exception as e:
    st.error(f"Could not load governance logs: {e}")
    gov_logs    = []
    gov_summary = {}
    ops_summary = {}

# Pull cost data from agent session if available
cost_summary = {}
if "agent" in st.session_state:
    try:
        cost_summary = st.session_state.agent.cost_controller.get_summary()
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# SECTION 1: 5-Pillar Summary Cards
# ════════════════════════════════════════════════════════════════
# Each card maps to one governance pillar.
# These are the "at a glance" metrics for the admin.

st.subheader("📊 5-Pillar Session Summary")
st.caption(
    "Each card represents one responsible AI pillar. "
    "Click tabs below for detail."
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    # ── PILLAR 1: Safety Guardrails ───────────────────────────
    blocked = gov_summary.get("total_blocked", 0)
    st.metric(
        label       = "🛡️ Guardrails",
        value       = f"{blocked} blocked",
        delta       = f"{gov_summary.get('output_flagged',0)} output flags",
        delta_color = "inverse" if blocked > 0 else "off"
    )

with col2:
    # ── PILLAR 2: Evaluation ──────────────────────────────────
    eval_logs   = get_logs_by_type("evaluation") if gov_logs is not None else []
    ops_score   = ops_summary.get("avg_evaluation_score", 0)
    eval_count  = ops_summary.get("total_evaluations", 0)
    # Also count real-time eval events from governance log
    rt_evals    = gov_summary.get("raw_counts", {}).get("EVAL_SCORED", 0)
    st.metric(
        label = "📊 Evaluation",
        value = f"{ops_score}/10" if ops_score else "N/A",
        delta = f"{rt_evals} real-time evals"
    )

with col3:
    # ── PILLAR 3: Audit Log ───────────────────────────────────
    total_events     = gov_summary.get("total_events", 0)
    high_risk_events = gov_summary.get("high_risk_events", 0)
    st.metric(
        label       = "📝 Audit Log",
        value       = f"{total_events} events",
        delta       = f"{high_risk_events} high-risk",
        delta_color = "inverse" if high_risk_events > 0 else "off"
    )

with col4:
    # ── PILLAR 4: Cost Controls ───────────────────────────────
    if cost_summary:
        pct   = cost_summary.get("pct_used", 0)
        cost  = cost_summary.get("total_cost_usd", 0)
        state = cost_summary.get("state", "OK")
        st.metric(
            label       = "💰 Cost Controls",
            value       = f"{pct:.1f}% used",
            delta       = f"${cost:.4f}",
            delta_color = "inverse" if state != "OK" else "off"
        )
    else:
        st.metric(label="💰 Cost Controls", value="No session", delta="Start chatting")

with col5:
    # ── PILLAR 5: Human-in-the-Loop ───────────────────────────
    hitl_triggered = gov_summary.get("hitl_triggered", 0)
    hitl_approved  = gov_summary.get("hitl_approved", 0)
    hitl_rejected  = gov_summary.get("hitl_rejected", 0)
    st.metric(
        label = "👤 HITL",
        value = f"{hitl_triggered} triggered",
        delta = f"{hitl_approved} ✅ · {hitl_rejected} ❌"
    )

st.divider()


# ════════════════════════════════════════════════════════════════
# SECTION 2: Per-Pillar Detail Tabs
# ════════════════════════════════════════════════════════════════
# One tab per pillar for deep-dive detail.
# Admin can navigate to any pillar for full information.

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🛡️ Pillar 1 — Guardrails",
    "📊 Pillar 2 — Evaluation",
    "📝 Pillar 3 — Audit Log",
    "💰 Pillar 4 — Cost Controls",
    "👤 Pillar 5 — HITL",
])


# ── TAB 1: SAFETY GUARDRAILS ─────────────────────────────────
with tab1:
    st.markdown("""
    **Pillar 1 — Safety Guardrails**

    Two-stage defence:
    - **Input guardrail** runs *before* the LLM — blocks PII and harmful queries instantly (zero token cost)
    - **Output guardrail** runs *after* the LLM — appends safety disclaimers when dosage content is detected

    *Files: `governance/guardrails.py`*
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Inputs Blocked",  gov_summary.get("total_blocked", 0))
    c2.metric("🔐 PII Detected",    gov_summary.get("pii_detected",  0))
    c3.metric("⚠️ Outputs Flagged", gov_summary.get("output_flagged",0))

    # Filter guardrail events from audit log
    guard_events = [
        e for e in gov_logs
        if e.get("event_type") in
           ("INPUT_BLOCKED", "PII_DETECTED", "OUTPUT_FLAGGED")
    ]

    if guard_events:
        st.markdown("#### Guardrail Event Log")
        for ev in guard_events[:20]:
            ts    = ev.get("timestamp", "")[:19].replace("T", " ")
            etype = ev.get("event_type", "")
            pii   = ev.get("pii_detected", "")
            det   = ev.get("details", "")
            color = "🔴" if "BLOCKED" in etype or "PII" in etype else "🟡"
            with st.expander(
                f"{color} `{etype}` — {ts}", expanded=False
            ):
                if pii:
                    st.markdown(f"**PII Type:** `{pii}`")
                st.markdown(f"**Detail:** {det}")
                if ev.get("query_preview"):
                    st.markdown(
                        f"**Query (masked):** `{ev['query_preview']}`"
                    )
    else:
        st.info(
            "No guardrail events yet. Try the demo queries in "
            "the Chat Assistant to trigger this pillar."
        )


# ── TAB 2: EVALUATION ────────────────────────────────────────
with tab2:
    st.markdown("""
    **Pillar 2 — Evaluation (LLM-as-Judge)**

    Real-time evaluation scores every AI response on 5 dimensions:
    Relevance · Accuracy · Completeness · Clarity · Safety

    - **V3:** Batch evaluation only (Evaluation page, 8 test cases)
    - **V4 addition:** Every chat response is scored in real time and the score appears inline

    *Files: `evaluation/evaluator.py` (unchanged), wired in `pages/8_Chat_Assistant.py`*
    """)

    eval_entries = get_logs_by_type("evaluation")
    rt_eval_events = [
        e for e in gov_logs if e.get("event_type") == "EVAL_SCORED"
    ]

    c1, c2 = st.columns(2)
    c1.metric(
        "Avg Batch Score",
        f"{ops_summary.get('avg_evaluation_score', 'N/A')}/10"
    )
    c2.metric("Real-time Evals This Session", len(rt_eval_events))

    if rt_eval_events:
        st.markdown("#### Real-time Evaluation Log")
        for ev in rt_eval_events[:15]:
            ts  = ev.get("timestamp", "")[:19].replace("T", " ")
            det = ev.get("details", "")
            st.markdown(f"- `{ts}` — {det}")
    else:
        st.info(
            "No real-time eval events yet. Chat with the assistant "
            "to see live scores appear here."
        )

    if eval_entries:
        st.markdown("#### Batch Evaluation History")
        st.dataframe(
            [
                {
                    "Time":           e.get("timestamp","")[:19],
                    "Query":          e.get("query","")[:50],
                    "Overall Score":  e.get("overall_score",""),
                }
                for e in eval_entries[-10:]
            ],
            width='stretch'
        )


# ── TAB 3: AUDIT LOG ─────────────────────────────────────────
with tab3:
    st.markdown("""
    **Pillar 3 — Audit Logging & Observability**

    Every governance event is persisted to `data/interaction_logs.json`
    with full metadata: timestamp, session, tool, risk level, PII flag, decision.

    - **V3 had:** interaction logs + tool call logs + evaluation logs
    - **V4 adds:** `governance_event` log type for all 5 pillars

    *Files: `evaluation/logger.py` — `log_governance_event()` is the V4 addition*
    """)

    # Filters
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        filter_type = st.selectbox(
            "Filter by event type",
            ["All", "INPUT_BLOCKED", "PII_DETECTED", "OUTPUT_FLAGGED",
             "EVAL_SCORED", "HITL_TRIGGERED", "HITL_APPROVED",
             "HITL_REJECTED", "HITL_EDITED", "COST_WARNING", "COST_HARD_STOP"],
        )
    with col_f2:
        filter_risk = st.selectbox(
            "Filter by risk level",
            ["All", "HIGH", "MEDIUM", "LOW"]
        )

    filtered = gov_logs
    if filter_type != "All":
        filtered = [e for e in filtered if e.get("event_type") == filter_type]
    if filter_risk != "All":
        filtered = [e for e in filtered if e.get("risk_level") == filter_risk]

    if filtered:
        rows = []
        for e in filtered[:50]:
            rows.append({
                "Time":       e.get("timestamp", "")[:19].replace("T", " "),
                "Event":      e.get("event_type", ""),
                "Tool":       e.get("tool_name", "—"),
                "Risk":       e.get("risk_level", ""),
                "PII":        e.get("pii_detected", "—"),
                "Detail":     e.get("details", "")[:80],
                "Decision":   e.get("decision", "—"),
            })
        st.dataframe(rows, width='stretch', height=400)
        st.caption(f"Showing {len(rows)} of {len(gov_logs)} governance events")
    else:
        st.info(
            "No governance events match the filter. "
            "Interact with the Chat Assistant to generate events."
        )

    # Also show V3 operational logs summary
    with st.expander("📈 V3 Operational Logs Summary"):
        st.json(ops_summary)


# ── TAB 4: COST CONTROLS ─────────────────────────────────────
with tab4:
    st.markdown("""
    **Pillar 4 — Cost Controls**

    Token budget enforcement prevents runaway API costs.

    States: **🟢 OK** → **🟡 WARNING** (70% of budget) → **🔴 HARD STOP** (100%)

    - **V3:** No cost tracking
    - **V4 adds:** `CostController` class with session-scoped budget

    *Files: `governance/cost_controller.py` — entirely new in V4*
    """)

    if cost_summary:
        state = cost_summary.get("state", "OK")
        pct   = cost_summary.get("pct_used", 0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tokens Used",    f"{cost_summary.get('total_tokens',0):,}")
        c2.metric("Session Cost",   f"${cost_summary.get('total_cost_usd',0):.4f}")
        c3.metric("Queries",        cost_summary.get("query_count", 0))
        c4.metric("Budget State",   state)

        st.markdown("#### Session Budget Gauge")
        bar_val = min(pct / 100, 1.0)
        st.progress(bar_val)
        st.caption(
            f"{pct:.1f}% of {cost_summary['hard_stop_threshold']:,} "
            f"token budget used · "
            f"Warning at {cost_summary['warning_threshold']:,} tokens"
        )

        # Per-query token breakdown
        query_log = cost_summary.get("query_log", [])
        if query_log:
            st.markdown("#### Token Usage per Query")
            st.dataframe(
                [
                    {
                        "#":        r["query_num"],
                        "Query":    r["query"],
                        "Tokens":   r["tokens"],
                        "Cost":     f"${r['cost_usd']:.5f}",
                        "Running":  f"{r['cumulative']:,}",
                    }
                    for r in query_log
                ],
                width='stretch'
            )
    else:
        st.info(
            "No active agent session found. "
            "Open the Chat Assistant to start a session, "
            "then return here to see cost metrics."
        )

    # Cost warning/stop events from audit log
    cost_events = [
        e for e in gov_logs
        if e.get("event_type") in ("COST_WARNING", "COST_HARD_STOP")
    ]
    if cost_events:
        st.markdown("#### Cost Governance Events")
        for ev in cost_events:
            ts  = ev.get("timestamp","")[:19].replace("T"," ")
            etype = ev.get("event_type","")
            icon  = "🛑" if etype == "COST_HARD_STOP" else "⚠️"
            st.markdown(f"- {icon} `{ts}` — {ev.get('details','')}")


# ── TAB 5: HUMAN-IN-THE-LOOP ─────────────────────────────────
with tab5:
    st.markdown("""
    **Pillar 5 — Human-in-the-Loop (HITL)**

    HIGH RISK tools (write/modify/delete) require explicit human approval.
    The agent pauses, shows an Approve / Reject / Edit widget, and
    only proceeds after a human decision.

    - **V3:** Agent executed all tools automatically
    - **V4 adds:** `classify_risk()` gate + `HITLInterrupt` exception
                   + approval widget in the chat page

    *Files: `governance/hitl_manager.py` (new) + `agent.py` (modified) + `pages/8_Chat_Assistant.py` (modified)*
    """)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Triggered",  gov_summary.get("hitl_triggered", 0))
    c2.metric("✅ Approved", gov_summary.get("hitl_approved",  0))
    c3.metric("❌ Rejected", gov_summary.get("hitl_rejected",  0))
    c4.metric("✏️ Edited",   gov_summary.get("hitl_edited",    0))

    # HITL event log
    hitl_events = [
        e for e in gov_logs
        if e.get("event_type", "").startswith("HITL_")
    ]

    if hitl_events:
        st.markdown("#### HITL Event Log")
        for ev in hitl_events[:20]:
            ts    = ev.get("timestamp","")[:19].replace("T"," ")
            etype = ev.get("event_type","")
            tool  = ev.get("tool_name","—")
            dec   = ev.get("decision","")
            det   = ev.get("details","")

            if "APPROVED" in etype or "EDITED" in etype:
                icon = "✅"
            elif "REJECTED" in etype:
                icon = "❌"
            else:
                icon = "⚠️"

            with st.expander(
                f"{icon} `{etype}` — `{tool}` — {ts}", expanded=False
            ):
                st.markdown(f"**Decision:** {dec or '(pending)'}")
                st.markdown(f"**Detail:** {det}")
    else:
        st.info(
            "No HITL events yet. Try the **👤 HITL Demo** button "
            "in the Chat Assistant sidebar to trigger a HITL approval."
        )

st.divider()

# ── Refresh button ────────────────────────────────────────────
if st.button("🔄 Refresh Dashboard"):
    st.rerun()

st.caption(
    "Governance Dashboard · V4 · Anil Pathak's Agentic Healthcare Assistant · "
    "IEEE Session 5 — Responsible & Safe Agentic AI"
)
