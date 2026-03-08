# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/8_Chat_Assistant.py
# Purpose       : AI Chat Assistant — the primary end-user
#                 interface to the Healthcare Agent.
#
# ══════════════════════════════════════════════════════════════
# V3 vs V4 CHANGES IN THIS FILE
# ══════════════════════════════════════════════════════════════
# This file is MODIFIED from V3.  All V4 additions are marked
# with [V4 · PILLAR N] comments.
#
# KEY DESIGN PRINCIPLE:
#   Governance is INVISIBLE to patients but VISIBLE to admins.
#   From a patient's perspective this is just a chat window.
#   The governance machinery (guardrails, cost meter, eval score,
#   HITL widget) appears inline but is unobtrusive.
#
# V4 UI additions:
#
#   [PILLAR 1 · GUARDRAILS]
#     • Blocked messages shown with red banner in chat
#     • No separate page needed — appears inline in chat
#
#   [PILLAR 2 · EVALUATION]
#     • Real-time eval score badge (⭐ x.x/10) shown under
#       every AI response — wired to ResponseEvaluator
#     • Runs asynchronously after each response
#
#   [PILLAR 4 · COST CONTROLS]
#     • Token budget meter in right-side info panel
#     • Colour: green (OK) → orange (WARNING) → red (HARD STOP)
#     • Budget state shown as text alongside the progress bar
#
#   [PILLAR 5 · HITL]
#     • HITLInterrupt caught from agent.chat()
#     • Pending action stored in st.session_state["hitl_pending"]
#     • Approve / Reject / Edit widget appears above chat input
#     • Chat input DISABLED while approval is pending
#     • Decision logged via log_governance_event()
#
#   PILLAR 3 (Audit Log) is handled inside agent.py and logger.py
#   — no separate UI needed in the chat page.
# ══════════════════════════════════════════════════════════════

import streamlit as st
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar

st.set_page_config(
    page_title="Chat Assistant",
    page_icon="💬",
    layout="wide"
)
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("💬 AI Healthcare Chat Assistant")
st.caption(
    "Powered by GPT-4o-mini · Agentic AI with Function Calling · "
    "🛡️ Responsible AI Governance Active"
)
st.divider()


# ── Session state initialisation ─────────────────────────────
# The agent is created once per browser session and cached in
# st.session_state so conversation memory persists across reruns.

if "agent" not in st.session_state:
    with st.spinner("Initialising Healthcare Agent…"):
        from agent import HealthcareAgent
        from tools.rag_tool import build_vector_store
        build_vector_store()
        st.session_state.agent = HealthcareAgent(
            session_id    = f"chat_{int(time.time())}",
            enable_logging= True
        )

if "chat_messages"  not in st.session_state:
    st.session_state.chat_messages = []
if "tool_traces"    not in st.session_state:
    st.session_state.tool_traces = []

# [V4 · PILLAR 5 · HITL] — Pending action state
# When agent raises HITLInterrupt, the pending action is stored
# here.  While this is set, the chat input is disabled and the
# HITL approval widget is shown.
if "hitl_pending" not in st.session_state:
    st.session_state.hitl_pending = None

# [V4 · PILLAR 2 · EVALUATION] — Track last eval score for display
if "last_eval_score" not in st.session_state:
    st.session_state.last_eval_score = None


# ── Two-column layout: chat (left) | info panel (right) ───────
chat_col, info_col = st.columns([2, 1])


# ════════════════════════════════════════════════════════════════
# LEFT COLUMN — Chat interface
# ════════════════════════════════════════════════════════════════
with chat_col:

    # ── Render conversation history ───────────────────────────
    for msg in st.session_state.chat_messages:
        avatar = "🧑" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

            # Show eval score badge under assistant messages (if stored)
            if msg["role"] == "assistant" and msg.get("eval_score"):
                score = msg["eval_score"]
                color = "green" if score >= 8.5 else "orange" if score >= 7 else "red"
                st.caption(
                    f"⭐ Quality Score: **{score}/10** &nbsp;|&nbsp; "
                    f"🛡️ Governance Active"
                )

            # Show tool usage caption under assistant messages
            if msg["role"] == "assistant" and msg.get("tools_used"):
                tools_str = ", ".join(f"`{t}`" for t in msg["tools_used"])
                st.caption(f"🔧 Tools used: {tools_str}")

    # ─────────────────────────────────────────────────────────
    # [V4 · PILLAR 5 · HITL] — Approval widget
    # ─────────────────────────────────────────────────────────
    # BEFORE V4: this block did not exist.
    # AFTER  V4: when hitl_pending is set, show the approval
    #            widget ABOVE the chat input.  The chat input
    #            is disabled until a decision is made.
    if st.session_state.hitl_pending:
        pending = st.session_state.hitl_pending
        st.warning(
            f"⚠️ **Human Approval Required** — The agent wants to perform "
            f"a HIGH RISK action that modifies patient data."
        )
        with st.expander("📋 Review Proposed Action", expanded=True):
            col_k, col_v = st.columns([1, 2])
            with col_k:
                st.markdown("**Tool**")
                st.markdown("**Description**")
                for k in pending.get("tool_args", {}).keys():
                    st.markdown(f"**{k}**")
            with col_v:
                st.code(pending["tool_name"])
                st.markdown(pending["description"])
                for v in pending.get("tool_args", {}).values():
                    st.markdown(f"`{v}`")

        approve_col, reject_col, edit_col = st.columns(3)

        with approve_col:
            if st.button("✅ Approve", type="primary", width='stretch'):
                _result = st.session_state.agent.execute_approved_hitl_action(
                    tool_name    = pending["tool_name"],
                    tool_args    = pending["tool_args"],
                    decision     = "APPROVED",
                    tool_call_id = pending.get("tool_call_id", ""),
                )
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": _result,
                    "tools_used": [pending["tool_name"]],
                })
                st.session_state.hitl_pending = None
                st.rerun()

        with reject_col:
            if st.button("❌ Reject", width='stretch'):
                # Log the rejection [PILLAR 3]
                try:
                    from evaluation.logger import log_governance_event
                    log_governance_event(
                        event_type = "HITL_REJECTED",
                        session_id = st.session_state.agent.session_id,
                        tool_name  = pending["tool_name"],
                        risk_level = "HIGH",
                        decision   = "REJECTED",
                        details    = "Rejected by user via chat UI",
                    )
                except Exception:
                    pass
                _reject_msg = (
                    f"❌ **Action Rejected**\n\n"
                    f"The requested action (`{pending['tool_name']}`) "
                    f"has been cancelled. The patient record has **not** "
                    f"been modified. This rejection has been logged to "
                    f"the audit trail."
                )
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": _reject_msg,
                })
                st.session_state.hitl_pending = None
                st.rerun()

        with edit_col:
            if st.button("✏️ Edit & Approve", width='stretch'):
                st.session_state["hitl_edit_mode"] = True
                st.rerun()

        # Edit mode — show text input for each arg
        if st.session_state.get("hitl_edit_mode"):
            st.markdown("**Edit the action arguments before approving:**")
            edited_args = {}
            for k, v in pending["tool_args"].items():
                edited_args[k] = st.text_input(
                    f"Edit `{k}`", value=str(v), key=f"edit_{k}"
                )
            if st.button("Confirm Edited Action", type="primary"):
                _result = st.session_state.agent.execute_approved_hitl_action(
                    tool_name    = pending["tool_name"],
                    tool_args    = edited_args,
                    decision     = "EDITED",
                    tool_call_id = pending.get("tool_call_id", ""),
                )
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": _result,
                    "tools_used": [pending["tool_name"]],
                })
                st.session_state.hitl_pending  = None
                st.session_state.hitl_edit_mode = False
                st.rerun()

        st.divider()

    # ── Chat input ────────────────────────────────────────────
    # Disabled while HITL approval is pending
    hitl_active    = st.session_state.hitl_pending is not None
    placeholder    = (
        "⚠️ Resolve the pending approval above before continuing…"
        if hitl_active
        else "Ask me about patients, appointments, or medical information…"
    )

    if user_input := st.chat_input(placeholder, disabled=hitl_active):

        # Add user message to history and render immediately
        st.session_state.chat_messages.append({
            "role": "user", "content": user_input
        })
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

        # ── Call the agent ────────────────────────────────────
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                start_t = time.time()
                response       = None
                hitl_triggered = False

                try:
                    response = st.session_state.agent.chat(
                        user_input, verbose=False
                    )
                except Exception as hitl_exc:
                    # [V4 · PILLAR 5 · HITL] — Catch HITLInterrupt
                    # The agent raised HITLInterrupt before executing
                    # a HIGH RISK tool.  Store the pending action and
                    # let the widget render on next rerun.
                    cls_name = type(hitl_exc).__name__
                    if cls_name == "HITLInterrupt" or hasattr(hitl_exc, "tool_name"):
                        st.session_state.hitl_pending = {
                            "tool_name":    hitl_exc.tool_name,
                            "tool_args":    hitl_exc.tool_args,
                            "tool_call_id": getattr(hitl_exc, "tool_call_id", ""),
                            "description": (
                                f"Modify patient data using "
                                f"`{hitl_exc.tool_name}`"
                            ),
                        }
                        hitl_triggered = True
                        response = (
                            f"⚠️ I need to perform a **HIGH RISK** action "
                            f"(`{hitl_exc.tool_name}`) that modifies patient "
                            f"data.  Please **review and approve** the action "
                            f"in the panel above before I proceed."
                        )
                    else:
                        response = f"❌ An error occurred: {hitl_exc}"

                elapsed       = round((time.time() - start_t) * 1000)
                tools_used    = st.session_state.agent.last_tools_used

            # Render the response
            st.markdown(response)

            # [V4 · PILLAR 2 · EVALUATION] — Real-time eval score
            # ─────────────────────────────────────────────────
            # BEFORE V4: eval only ran as a batch on the Evaluation page.
            # AFTER  V4: every non-blocked, non-HITL response is scored
            #            inline using ResponseEvaluator.
            eval_score = None
            if (response and not hitl_triggered
                    and not response.startswith(("🔐", "🚫", "🛑", "⚠️"))):
                try:
                    from evaluation.evaluator import ResponseEvaluator
                    _evaluator = ResponseEvaluator()
                    _eval_result = _evaluator.evaluate_response(
                        query    = user_input,
                        response = response,
                    )
                    if _eval_result.get("status") == "success":
                        eval_score = _eval_result["scores"].get("overall", None)
                        st.session_state.last_eval_score = eval_score

                        # Log EVAL_SCORED governance event [PILLAR 3]
                        try:
                            from evaluation.logger import log_governance_event
                            log_governance_event(
                                event_type    = "EVAL_SCORED",
                                session_id    = st.session_state.agent.session_id,
                                query_preview = user_input[:100],
                                risk_level    = "LOW",
                                details       = (
                                    f"Score {eval_score}/10 | "
                                    f"Safety: "
                                    f"{_eval_result['scores'].get('safety', 'N/A')}"
                                ),
                            )
                        except Exception:
                            pass
                except Exception:
                    pass  # Eval failure must never break the chat

            # Show score badge + tool usage caption
            caption_parts = [f"⏱️ {elapsed}ms"]
            if eval_score is not None:
                caption_parts.append(f"⭐ Score: **{eval_score}/10**")
            if tools_used:
                caption_parts.append(
                    f"🔧 Tools: {', '.join(tools_used)}"
                )
            if hitl_triggered:
                caption_parts.append("👤 **HITL Pending**")
            st.caption(" &nbsp;|&nbsp; ".join(caption_parts))

        # Save message with metadata
        st.session_state.chat_messages.append({
            "role":       "assistant",
            "content":    response,
            "tools_used": tools_used,
            "eval_score": eval_score,
        })

        # Update tool trace log for sidebar display
        if tools_used:
            st.session_state.tool_traces.append({
                "query":   user_input[:60],
                "tools":   tools_used,
                "time_ms": elapsed
            })

        st.rerun()


# ════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Info panel
# ════════════════════════════════════════════════════════════════
with info_col:

    # ─────────────────────────────────────────────────────────
    # [V4 · PILLAR 4 · COST CONTROLS] — Token budget meter
    # ─────────────────────────────────────────────────────────
    # BEFORE V4: this section did not exist.
    # AFTER  V4: live token budget meter shown for every session.
    #            Colour transitions: green → orange → red.
    st.subheader("💰 Token Budget")
    budget = st.session_state.agent.cost_controller.check_budget()
    pct    = budget["pct_used"] / 100

    # Colour-coded progress bar
    if budget["state"] == "OK":
        bar_color = "normal"   # Streamlit green
    elif budget["state"] == "WARNING":
        bar_color = "normal"   # We style with text below
    else:
        bar_color = "normal"

    st.progress(pct)

    state_emoji = {"OK": "🟢", "WARNING": "🟡", "HARD_STOP": "🔴"}
    st.caption(
        f"{state_emoji.get(budget['state'], '🔵')} "
        f"{budget['tokens_used']:,} / "
        f"{st.session_state.agent.cost_controller.hard_stop_threshold:,} tokens "
        f"(${budget['cost_usd']:.4f})"
    )
    if budget["state"] == "WARNING":
        st.warning(budget["message"], icon="⚠️")
    elif budget["state"] == "HARD_STOP":
        st.error(budget["message"], icon="🛑")

    st.divider()

    # ── Tool Activity (V3 — unchanged) ───────────────────────
    st.subheader("🔧 Tool Activity")
    if st.session_state.tool_traces:
        for trace in reversed(st.session_state.tool_traces[-5:]):
            with st.expander(f"💬 {trace['query']}…", expanded=False):
                for tool in trace["tools"]:
                    st.markdown(f"• `{tool}`")
                st.caption(f"⏱️ {trace['time_ms']}ms")
    else:
        st.info("Tool usage will appear here as you chat.")

    st.divider()

    # ── Active Patient Context (V3 — unchanged) ──────────────
    st.subheader("🧠 Active Patient")
    patient_ctx = st.session_state.agent.memory.get_patient_context()
    if patient_ctx:
        for k, v in patient_ctx.items():
            val = str(v).strip()
            if val and val not in ["N/A", "nan", "None", ""]:
                st.markdown(f"**{k}:** {val[:40]}")
    else:
        st.info("No active patient context.")

    st.divider()

    # ─────────────────────────────────────────────────────────
    # [V4 · PILLAR 2 · EVALUATION] — Last response score
    # ─────────────────────────────────────────────────────────
    # BEFORE V4: eval score only visible on Evaluation page.
    # AFTER  V4: last eval score shown inline in the chat sidebar.
    if st.session_state.last_eval_score is not None:
        st.subheader("📊 Last Response Quality")
        score = st.session_state.last_eval_score
        color = "green" if score >= 8.5 else "orange" if score >= 7 else "red"
        st.metric(label="LLM-as-Judge Score", value=f"{score} / 10")
        st.caption("Evaluated on: Relevance · Accuracy · Completeness · Clarity · Safety")
        st.divider()

    # ── Quick Queries (V3 — unchanged, extended with demo chips) ─
    st.subheader("⚡ Quick Queries")
    quick_queries = [
        "Show all patients",
        "Find a cardiologist",
        "Summarise Anjali's history",
        "Latest diabetes treatments",
        "Ramesh Kulkarni medications",
    ]
    for q in quick_queries:
        if st.button(q, width='stretch', key=f"q_{q}"):
            st.session_state.chat_messages.append(
                {"role": "user", "content": q}
            )
            with st.spinner("Processing…"):
                try:
                    _resp = st.session_state.agent.chat(q, verbose=False)
                except Exception as _e:
                    cls = type(_e).__name__
                    if cls == "HITLInterrupt" or hasattr(_e, "tool_name"):
                        st.session_state.hitl_pending = {
                            "tool_name":    _e.tool_name,
                            "tool_args":    _e.tool_args,
                            "tool_call_id": getattr(_e, "tool_call_id", ""),
                            "description": f"Modify data via `{_e.tool_name}`",
                        }
                        _resp = "⚠️ HITL approval required. See panel above."
                    else:
                        _resp = f"Error: {_e}"
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": _resp}
            )
            st.rerun()

    # ─────────────────────────────────────────────────────────
    # [V4 · PILLAR 1 · GUARDRAILS] — Demo chips
    # ─────────────────────────────────────────────────────────
    # BEFORE V4: no governance demo shortcuts existed.
    # AFTER  V4: shortcut chips to trigger each governance pillar
    #            live during the IEEE Session 5 demonstration.
    st.divider()
    st.subheader("🛡️ Governance Demos")
    st.caption("Try these to see each pillar in action:")

    # BEFORE V4: 3 demo chips — SSN PII, harmful query, HITL.
    # AFTER  V4: 6 demo chips covering all governance pillars:
    #   • PII Demo        — Aadhaar (India-relevant identifier)
    #   • Harmful Query   — lethal dose → BLOCKED by guardrail
    #   • Safe Clinical   — toxic effects → PASSES (shows boundary)
    #   • Output Safety   — dosage response → safety footer appended
    #   • HITL High Risk  — write operation → approval widget appears
    #   • HITL Low Risk   — read operation  → executes directly (contrast)
    demo_queries = [
        ("🔐 PII — Aadhaar",       "My Aadhaar is 2345 6789 0123, please book an appointment for me"),
        ("🚫 Harmful Query",        "What is the lethal dose of paracetamol?"),
        ("✅ Safe Clinical Query",   "What are the toxic effects of paracetamol overdose?"),
        ("💊 Output Safety Footer", "What is the usual dose of Metformin for diabetes?"),
        ("👤 HITL — High Risk",     "Update Anjali Mehra diagnosis to Type 2 Diabetes"),
        ("👁️ HITL — Low Risk",      "Show me Anjali Mehra's appointments"),
    ]
    for label, query in demo_queries:
        if st.button(label, width='stretch', key=f"demo_{label}"):
            st.session_state.chat_messages.append(
                {"role": "user", "content": query}
            )
            with st.spinner("Processing…"):
                try:
                    _resp = st.session_state.agent.chat(query, verbose=False)
                except Exception as _e:
                    cls = type(_e).__name__
                    if cls == "HITLInterrupt" or hasattr(_e, "tool_name"):
                        st.session_state.hitl_pending = {
                            "tool_name":    _e.tool_name,
                            "tool_args":    _e.tool_args,
                            "tool_call_id": getattr(_e, "tool_call_id", ""),
                            "description": f"Modify data via `{_e.tool_name}`",
                        }
                        _resp = "⚠️ HITL approval required. See panel above."
                    else:
                        _resp = f"Error: {_e}"
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": _resp}
            )
            st.rerun()

    st.divider()

    # ── Reset (V3 base, V4 also resets cost + governance state) ─
    if st.button("🔄 Reset Conversation", width='stretch'):
        st.session_state.agent.reset_session()
        st.session_state.chat_messages  = []
        st.session_state.tool_traces    = []
        st.session_state.hitl_pending   = None    # [V4 · PILLAR 5]
        st.session_state.last_eval_score= None    # [V4 · PILLAR 2]
        st.session_state.pop("hitl_edit_mode", None)
        st.rerun()
