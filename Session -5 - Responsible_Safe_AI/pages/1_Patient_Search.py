# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/1_Patient_Search.py
# Purpose       : Patient Section — Patient Search & History page.
#                 Allows searching patient records by name or ID,
#                 viewing full record details and appointments,
#                 and generating AI-powered medical history
#                 summaries using RAG (FAISS + GPT-4o-mini).
# =============================================================

import streamlit as st
import json
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from tools.patient_db_tool import get_patient_by_name, list_all_patients, get_patient_by_id
from tools.appointment_tool import get_patient_appointments
from tools.rag_tool import retrieve_patient_history

st.set_page_config(page_title="Patient Search", page_icon="👤", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "patient"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("👤 Patient Search & Medical History")
st.caption("Patient Section")
st.divider()


def safe_df(data):
    """
    Convert all DataFrame columns to string to prevent PyArrow
    serialisation errors when rendering in Streamlit.

    Args:
        data (list): List of dicts to convert to DataFrame.

    Returns:
        pd.DataFrame: DataFrame with all columns cast to str.
    """
    df = pd.DataFrame(data)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df


tab1, tab2, tab3 = st.tabs(["🔍 Search Patient", "📋 All Patients", "📄 Medical History (RAG)"])

# ── Tab 1: Search patient by name or ID ──────────────────────
with tab1:
    st.subheader("Search Patient Record")
    col1, col2 = st.columns([3, 1])
    with col1:
        search_input = st.text_input("Enter patient name or ID",
                                     placeholder="e.g. Anjali, David, P001")
    with col2:
        search_type = st.selectbox("Search by", ["Name", "ID"])

    if st.button("🔍 Search", type="primary"):
        if search_input.strip():
            with st.spinner("Searching..."):
                if search_type == "Name":
                    result = json.loads(get_patient_by_name(search_input.strip()))
                else:
                    result = json.loads(get_patient_by_id(search_input.strip()))

            if result.get("status") == "success":
                patients = result.get("patients") or [result.get("patient")]
                for p in [x for x in patients if x]:
                    pname = p.get("Name", p.get("name", "Unknown"))
                    st.success(f"Found: {pname}")

                    with st.expander("📋 Patient Details", expanded=True):
                        cols = st.columns(3)
                        items = [(k, v) for k, v in p.items()
                                 if str(v).strip() not in ["", "N/A", "nan", "None"]]
                        for i, (k, v) in enumerate(items):
                            cols[i % 3].metric(label=k, value=str(v)[:50])

                    # Show appointments for this patient
                    pid = str(p.get("Patient_ID", p.get("patient_id", "")))
                    if pid and pid not in ["", "N/A", "nan"]:
                        appt_result = json.loads(get_patient_appointments(pid))
                        if appt_result.get("status") == "success":
                            st.subheader("📅 Appointments")
                            appts = appt_result.get("appointments", [])
                            if appts:
                                st.dataframe(safe_df(appts), width='stretch')
                            else:
                                st.info("No appointments booked yet.")
            else:
                st.warning(result.get("message", "Patient not found."))
        else:
            st.warning("Please enter a name or ID to search.")

# ── Tab 2: All patients ───────────────────────────────────────
with tab2:
    st.subheader("All Patients")
    if st.button("📋 Load All Patients", type="primary"):
        with st.spinner("Loading..."):
            result = json.loads(list_all_patients())
        if result.get("status") == "success":
            patients = result.get("patients", [])
            st.success(f"Total patients: {len(patients)}")
            st.dataframe(safe_df(patients), width='stretch')
        else:
            st.error(result.get("message", "Failed to load patients."))

# ── Tab 3: RAG-based medical history summary ──────────────────
with tab3:
    st.subheader("Medical History — AI Summary (RAG)")
    st.info(
        "Uses FAISS vector store over patient PDF reports to retrieve "
        "and summarise medical history with GPT-4o-mini."
    )

    patient_name = st.text_input("Patient name",
                                  placeholder="e.g. Anjali Mehra, David Thompson")
    custom_query = st.text_input(
        "Specific question (optional)",
        placeholder="e.g. What medications is this patient currently on?"
    )

    if st.button("📄 Generate Medical Summary", type="primary"):
        if patient_name.strip():
            with st.spinner("Retrieving and summarising medical history..."):
                result = json.loads(retrieve_patient_history(
                    patient_name=patient_name.strip(),
                    query=custom_query.strip() if custom_query.strip() else ""
                ))
            if result.get("status") == "success":
                st.success("Summary generated successfully!")
                st.markdown("### 📋 Medical Summary")
                st.markdown(result.get("summary", "No summary available."))
                sources = result.get("sources", [])
                if sources:
                    st.caption(f"Sources: {', '.join(sources)}")
            else:
                st.error(result.get("message", "Could not retrieve history."))
        else:
            st.warning("Please enter a patient name.")
