# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : streamlit_app.py
# Purpose       : Main entry point and home page.
#                 Renders the role selector (Patient / Doctor-Admin).
#                 Sets st.session_state["role"] and navigates to
#                 the appropriate role dashboard.
#                 Sidebar is minimal on home — no role links shown
#                 until the user selects a role.
#                 Run with: python -m streamlit run streamlit_app.py
# =============================================================

import streamlit as st

st.set_page_config(
    page_title="Anil Pathak's Healthcare Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Minimal home sidebar ──────────────────────────────────────
st.sidebar.markdown("## 🏥 Healthcare Assistant")
st.sidebar.caption("Anil Pathak | Capstone Project")
st.sidebar.divider()
st.sidebar.page_link("streamlit_app.py",           label="🏠 Home")
st.sidebar.divider()
st.sidebar.page_link("pages/0_Patient_Dashboard.py", label="👤 Patient Section")
st.sidebar.divider()
st.sidebar.page_link("pages/0_Doctor_Dashboard.py",  label="🩺 Doctor / Admin Section")
st.sidebar.divider()
st.sidebar.page_link("pages/8_Chat_Assistant.py",    label="💬 Chat Assistant")
st.sidebar.divider()
st.sidebar.caption("GPT-4o-mini · LangChain · FAISS\nMedlinePlus · WHO · RAG")

# ── Page header ───────────────────────────────────────────────
st.title("🏥 Anil Pathak's — Agentic Healthcare Assistant")
st.caption("Capstone Project — Agentic Healthcare Assistant for Medical Task Automation")
st.divider()

# ── Role selector ─────────────────────────────────────────────
st.subheader("Welcome! Please select your role to continue.")
st.markdown(" ")

col_patient, col_spacer, col_admin = st.columns([5, 1, 5])

with col_patient:
    st.markdown("""
    <div style="
        background-color: #e8f4fd;
        border: 2px solid #3498db;
        border-radius: 14px;
        padding: 40px 30px;
        text-align: center;
    ">
        <div style="font-size: 3.5rem;">👤</div>
        <h2 style="margin: 12px 0 8px 0;">I am a Patient</h2>
        <p style="color: #555; font-size: 0.95rem;">
            Search patient records · Find doctors by specialty<br>
            Book and manage appointments
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(" ")
    if st.button("Enter Patient Section →",
                 width='stretch', type="primary", key="btn_patient"):
        st.session_state["role"] = "patient"
        st.switch_page("pages/0_Patient_Dashboard.py")

with col_admin:
    st.markdown("""
    <div style="
        background-color: #eafaf1;
        border: 2px solid #2ecc71;
        border-radius: 14px;
        padding: 40px 30px;
        text-align: center;
    ">
        <div style="font-size: 3.5rem;">🩺</div>
        <h2 style="margin: 12px 0 8px 0;">I am a Doctor / Admin</h2>
        <p style="color: #555; font-size: 0.95rem;">
            View doctor schedules · Manage patient records<br>
            Run evaluations and monitor analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(" ")
    if st.button("Enter Doctor / Admin Section →",
                 width='stretch', type="primary", key="btn_admin"):
        st.session_state["role"] = "admin"
        st.switch_page("pages/0_Doctor_Dashboard.py")

st.divider()

# ── Chat assistant shortcut ───────────────────────────────────
st.markdown("#### 💬 Or go directly to the AI Chat Assistant")
st.caption("Ask anything in natural language — patient lookup, appointments, medical information and more.")
if st.button("Open Chat Assistant", key="btn_chat"):
    st.switch_page("pages/8_Chat_Assistant.py")

st.divider()

# ── System capabilities ───────────────────────────────────────
st.markdown("#### System Capabilities")
st.markdown("""
| Feature | Technology |
|---|---|
| Agent Orchestration | OpenAI GPT-4o-mini with Function Calling |
| Medical History RAG | FAISS Vector Store + LangChain |
| Doctor Scheduling | Mock Doctor Schedule API (doctors.xlsx) |
| Patient Records | Excel DB (records.xlsx) — add / update support |
| Medical Information | MedlinePlus (NLM/NIH) + WHO (primary), DuckDuckGo (fallback) |
| Conversation Memory | Sliding Window + Active Patient Context |
| LLMOps Evaluation | LLM-as-Judge + Booking Success Rate + Module KPIs |
| Booking UX | Name-based — no Doctor ID or Patient ID required |
""")
