# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : utils/sidebar_helper.py
# Purpose       : Shared contextual sidebar renderer.
#                 Called by every page to render a role-aware
#                 sidebar. Reads st.session_state["role"] and
#                 expands only the relevant section links.
#                 Avoids duplicating sidebar code across 10 pages.
# =============================================================

import streamlit as st


def render_sidebar():
    """
    Render the contextual sidebar based on the current user role.

    Reads st.session_state["role"] which is set when the user
    clicks Enter on the home page. Shows:
      - Always: Home link, Chat Assistant link
      - Patient role: expanded Patient Section links
      - Admin role:   expanded Doctor/Admin Section links
      - No role set:  compact top-level links only

    Returns:
        None
    """
    role = st.session_state.get("role", None)

    st.sidebar.markdown("## 🏥 Healthcare Assistant")
    st.sidebar.caption("Anil Pathak | Capstone Project")
    st.sidebar.divider()

    # ── Home ─────────────────────────────────────────────────
    st.sidebar.page_link("streamlit_app.py", label="🏠 Home")
    st.sidebar.divider()

    # ── Patient Section ───────────────────────────────────────
    if role == "patient":
        # Expanded — user is in patient context
        st.sidebar.markdown("**👤 Patient Section**")
        st.sidebar.page_link("pages/0_Patient_Dashboard.py",  label="  📋 Patient Dashboard")
        st.sidebar.page_link("pages/1_Patient_Search.py",     label="  👤 Patient Search")
        st.sidebar.page_link("pages/2_Doctor_Search.py",      label="  🔍 Doctor Search")
        st.sidebar.page_link("pages/3_My_Appointments.py",    label="  📅 My Appointments")
    else:
        # Collapsed — show section entry point only
        st.sidebar.page_link("pages/0_Patient_Dashboard.py",  label="👤 Patient Section")

    st.sidebar.divider()

    # ── Doctor / Admin Section ────────────────────────────────
    if role == "admin":
        # Expanded — user is in admin context
        st.sidebar.markdown("**🩺 Doctor / Admin Section**")
        st.sidebar.page_link("pages/0_Doctor_Dashboard.py",   label="  🏠 Admin Dashboard")
        st.sidebar.page_link("pages/4_Doctor_Schedule.py",    label="  🗓️ Doctor Schedule")
        st.sidebar.page_link("pages/5_Medical_Records.py",    label="  📋 Medical Records")
        st.sidebar.page_link("pages/6_Model_Evaluation.py",   label="  📊 Model Evaluation")
        st.sidebar.page_link("pages/7_Logs_Analytics.py",     label="  📈 Logs & Analytics")
        # [V4 · PILLAR 3 · AUDIT LOG] — New governance link in admin sidebar
        # BEFORE V4: this link did not exist.
        # AFTER  V4: AI Governance & Safety is a first-class Admin section.
        st.sidebar.page_link("pages/9_AI_Governance.py",      label="  🛡️ AI Governance & Safety ✨")
    else:
        # Collapsed — show section entry point only
        st.sidebar.page_link("pages/0_Doctor_Dashboard.py",   label="🩺 Doctor / Admin Section")

    st.sidebar.divider()

    # ── Chat Assistant — always visible ──────────────────────
    st.sidebar.page_link("pages/8_Chat_Assistant.py",         label="💬 Chat Assistant")
    st.sidebar.divider()
    st.sidebar.caption("GPT-4o-mini · LangChain · FAISS\nMedlinePlus · WHO · RAG")
