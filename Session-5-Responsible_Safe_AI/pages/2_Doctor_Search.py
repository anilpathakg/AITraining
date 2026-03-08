# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/2_Doctor_Search.py
# Purpose       : Patient Section — Doctor Search page.
#                 Allows patients to browse and search for
#                 doctors by medical specialty. Displays doctor
#                 profiles including qualifications, experience,
#                 hospital, and consultation fee.
#                 Doctor IDs are never exposed to the patient.
# =============================================================

import streamlit as st
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from tools.appointment_tool import find_doctors_by_specialty, get_all_specialties

st.set_page_config(page_title="Doctor Search", page_icon="🔍", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "patient"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("🔍 Doctor Search")
st.caption("Patient Section — Find doctors by specialty")
st.divider()

# ── Specialty selector ────────────────────────────────────────
spec_result = json.loads(get_all_specialties())
specialties = spec_result.get(
    "specialties",
    ["General Physician", "Cardiologist", "Nephrologist", "Diabetologist"]
)

col1, col2 = st.columns([3, 1])
with col1:
    selected_spec = st.selectbox("Select Medical Specialty", specialties)
with col2:
    st.markdown("###")
    search_btn = st.button("🔍 Find Doctors", type="primary", width='stretch')

# ── Results ───────────────────────────────────────────────────
if search_btn:
    with st.spinner(f"Searching for {selected_spec} doctors..."):
        result = json.loads(find_doctors_by_specialty(selected_spec))

    if result.get("status") == "success":
        doctors = result.get("doctors", [])
        st.success(f"Found {len(doctors)} doctor(s) for **{selected_spec}**")

        for doc in doctors:
            with st.expander(
                f"🩺 {doc.get('name')} — {doc.get('hospital')}",
                expanded=True
            ):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Specialty",    doc.get("specialty", "N/A"))
                c2.metric("Experience",   f"{doc.get('experience_years', 'N/A')} yrs")
                c3.metric("Fee",          f"Rs. {doc.get('consultation_fee', 'N/A')}")
                c4.metric("Hospital",     doc.get("hospital", "N/A"))

                st.caption(f"📞 {doc.get('phone')}  |  ✉️ {doc.get('email')}")
                st.caption(f"🎓 {doc.get('qualification')}")

        # Prompt patient to go to My Appointments to book
        st.divider()
        st.info("To book an appointment with any of these doctors, go to **My Appointments** in the sidebar.")
        if st.button("Go to My Appointments →"):
            st.switch_page("pages/3_My_Appointments.py")

    else:
        st.warning(result.get("message", "No doctors found for this specialty."))
