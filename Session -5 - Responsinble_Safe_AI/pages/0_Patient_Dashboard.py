# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/0_Patient_Dashboard.py
# Purpose       : Patient Section hub dashboard.
#                 Displays 4 navigation cards in a 2x2 grid:
#                 Patient Search, Doctor Search, My Appointments,
#                 and Chat Assistant. Sets role to "patient" so
#                 the contextual sidebar expands patient links.
# =============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sidebar_helper import render_sidebar

st.set_page_config(
    page_title="Patient Section",
    page_icon="👤",
    layout="wide"
)

# Set role so sidebar expands patient links
st.session_state["role"] = "patient"

# Render contextual sidebar
render_sidebar()

# ── Page header ───────────────────────────────────────────────
st.title("👤 Patient Section")
st.caption("Select what you would like to do today")
st.divider()

# ── 2 × 2 card grid ──────────────────────────────────────────
# Row 1
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 32px 20px 16px 20px;
        text-align: center;
        min-height: 190px;
    ">
        <div style="font-size: 2.8rem; margin-bottom: 10px;">👤</div>
        <div style="font-weight: 700; font-size: 1.1rem;
                    margin-bottom: 6px;">Patient Search</div>
        <div style="font-size: 0.88rem; color: #555;">
            Search patient records and view medical history summaries
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Patient Search →", key="c1",
                 width='stretch', type="primary"):
        st.switch_page("pages/1_Patient_Search.py")

with col2:
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 32px 20px 16px 20px;
        text-align: center;
        min-height: 190px;
    ">
        <div style="font-size: 2.8rem; margin-bottom: 10px;">🔍</div>
        <div style="font-weight: 700; font-size: 1.1rem;
                    margin-bottom: 6px;">Doctor Search</div>
        <div style="font-size: 0.88rem; color: #555;">
            Find doctors by specialty and view their profiles
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Doctor Search →", key="c2",
                 width='stretch', type="primary"):
        st.switch_page("pages/2_Doctor_Search.py")

st.markdown(" ")

# Row 2
col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 32px 20px 16px 20px;
        text-align: center;
        min-height: 190px;
    ">
        <div style="font-size: 2.8rem; margin-bottom: 10px;">📅</div>
        <div style="font-weight: 700; font-size: 1.1rem;
                    margin-bottom: 6px;">My Appointments</div>
        <div style="font-size: 0.88rem; color: #555;">
            Book new appointments and cancel existing ones
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open My Appointments →", key="c3",
                 width='stretch', type="primary"):
        st.switch_page("pages/3_My_Appointments.py")

with col4:
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        border: 2px solid #3498db;
        border-radius: 12px;
        padding: 32px 20px 16px 20px;
        text-align: center;
        min-height: 190px;
    ">
        <div style="font-size: 2.8rem; margin-bottom: 10px;">💬</div>
        <div style="font-weight: 700; font-size: 1.1rem;
                    margin-bottom: 6px;">Chat Assistant</div>
        <div style="font-size: 0.88rem; color: #555;">
            Ask anything in natural language — AI-powered healthcare help
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Chat Assistant →", key="c4",
                 width='stretch', type="primary"):
        st.switch_page("pages/8_Chat_Assistant.py")
