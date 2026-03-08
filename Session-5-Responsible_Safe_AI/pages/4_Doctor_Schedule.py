# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/4_Doctor_Schedule.py
# Purpose       : Doctor/Admin Section — Doctor Schedule page.
#                 Allows a doctor or admin to select a doctor
#                 by name and view their complete appointment
#                 schedule, including booked and available slots.
#                 Doctor is selected by name — ID resolved internally.
# =============================================================

import streamlit as st
import json
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from tools.appointment_tool import (
    find_doctors_by_specialty,
    get_available_slots_for_doctor,
    get_all_specialties,
    get_doctor_schedule
)

st.set_page_config(page_title="Doctor Schedule", page_icon="🗓️", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "admin"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("🗓️ Doctor Schedule")
st.caption("Doctor / Admin Section — View appointment schedules by doctor name")
st.divider()


def safe_df(data):
    """
    Convert all DataFrame columns to string to prevent PyArrow errors.

    Args:
        data (list): List of dicts.

    Returns:
        pd.DataFrame: All columns cast to str.
    """
    df = pd.DataFrame(data)
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df


# ── Step 1: Select specialty to narrow down doctor list ───────
st.subheader("Step 1: Select Specialty")
spec_result = json.loads(get_all_specialties())
specialties = spec_result.get(
    "specialties",
    ["General Physician", "Cardiologist", "Nephrologist", "Diabetologist"]
)

col1, col2 = st.columns([3, 1])
with col1:
    selected_spec = st.selectbox("Medical Specialty", specialties)
with col2:
    st.markdown("###")
    if st.button("Load Doctors", type="primary", width='stretch'):
        with st.spinner("Loading doctors..."):
            doc_result = json.loads(find_doctors_by_specialty(selected_spec))
        if doc_result.get("status") == "success":
            st.session_state["schedule_doctors"] = doc_result.get("doctors", [])
        else:
            st.warning("No doctors found for this specialty.")

# ── Step 2: Select doctor by name ─────────────────────────────
if st.session_state.get("schedule_doctors"):
    st.divider()
    st.subheader("Step 2: Select Doctor by Name")

    doctors = st.session_state["schedule_doctors"]
    # Present doctors by name only — ID is resolved internally
    doc_labels = [
        f"{d['name']} — {d['hospital']} ({d['qualification']})"
        for d in doctors
    ]
    doc_idx = st.selectbox("Doctor", range(len(doc_labels)),
                            format_func=lambda i: doc_labels[i])
    selected_doc = doctors[doc_idx]

    col_a, col_b = st.columns([2, 1])
    with col_a:
        num_days = st.slider("Days ahead to show", 1, 30, 7)
    with col_b:
        st.markdown("###")
        view_btn = st.button("View Schedule", type="primary", width='stretch')

    if view_btn:
        with st.spinner(f"Loading schedule for {selected_doc['name']}..."):
            # Resolve doctor_id internally — admin sees name, not ID
            slots_result = json.loads(get_available_slots_for_doctor(
                doctor_id=selected_doc["doctor_id"],
                num_days=num_days
            ))

            # Also try to get full schedule including booked slots
            try:
                schedule_result = json.loads(get_doctor_schedule(selected_doc["doctor_id"]))
                booked_slots = [
                    s for s in schedule_result.get("schedule", [])
                    if s.get("status") == "booked"
                ]
            except Exception:
                booked_slots = []

        # ── Doctor summary card ───────────────────────────────
        st.divider()
        st.subheader(f"Schedule: {selected_doc['name']}")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Specialty",   selected_doc.get("specialty", "N/A"))
        mc2.metric("Hospital",    selected_doc.get("hospital", "N/A"))
        mc3.metric("Experience",  f"{selected_doc.get('experience_years', 'N/A')} yrs")
        mc4.metric("Fee",         f"Rs. {selected_doc.get('consultation_fee', 'N/A')}")

        # ── Available slots ───────────────────────────────────
        tab_avail, tab_booked = st.tabs(["✅ Available Slots", "📋 Booked Appointments"])

        with tab_avail:
            if slots_result.get("status") == "success":
                slots = slots_result.get("slots", [])
                if slots:
                    st.success(f"{len(slots)} available slots in next {num_days} days")
                    # Group by date for a clean calendar-style view
                    dates = {}
                    for s in slots:
                        d = s.get("date", "Unknown")
                        if d not in dates:
                            dates[d] = []
                        dates[d].append(s)

                    for date, day_slots in sorted(dates.items()):
                        with st.expander(
                            f"📅 {date} ({day_slots[0].get('day', '')}) — "
                            f"{len(day_slots)} slot(s)",
                            expanded=True
                        ):
                            time_cols = st.columns(min(len(day_slots), 4))
                            for i, s in enumerate(day_slots):
                                time_cols[i % 4].info(s.get("time", ""))
                else:
                    st.info(f"No available slots in the next {num_days} days.")
            else:
                st.warning(slots_result.get("message", "Could not load slots."))

        with tab_booked:
            if booked_slots:
                st.info(f"{len(booked_slots)} booked appointment(s)")
                booked_display = []
                for s in booked_slots:
                    booked_display.append({
                        "Date":         s.get("date", ""),
                        "Day":          s.get("day", ""),
                        "Time":         s.get("time", ""),
                        "Patient Name": s.get("patient_name", ""),
                        "Patient ID":   s.get("patient_id", ""),
                        "Slot ID":      s.get("slot_id", "")
                    })
                st.dataframe(safe_df(booked_display), width='stretch')
            else:
                st.info("No booked appointments found in this period.")
