# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/3_My_Appointments.py
# Purpose       : Patient Section — My Appointments page.
#                 Enables patients to book new appointments and
#                 cancel existing ones using name-based search.
#                 Doctor IDs and Patient IDs are resolved
#                 internally — patients never see or type them.
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
    book_appointment,
    cancel_appointment,
    get_all_specialties,
    get_patient_appointments
)
from tools.patient_db_tool import get_patient_by_name

st.set_page_config(page_title="My Appointments", page_icon="📅", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "patient"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("📅 My Appointments")
st.caption("Patient Section — Book and manage appointments")
st.divider()

tab1, tab2 = st.tabs(["📝 Book Appointment", "❌ Cancel Appointment"])

# ── Tab 1: Book Appointment ───────────────────────────────────
with tab1:
    st.subheader("Book a New Appointment")
    st.info("Search by your name and select a doctor — no IDs required.")

    col1, col2 = st.columns(2)

    # Step 1 — Identify the patient by name
    with col1:
        st.markdown("**Step 1: Find Your Record**")
        patient_search = st.text_input("Your name", placeholder="e.g. Anjali, David, Ramesh")

        if st.button("Search My Record", key="search_patient_btn"):
            if patient_search.strip():
                with st.spinner("Searching..."):
                    result = json.loads(get_patient_by_name(patient_search.strip()))
                if result.get("status") == "success":
                    patients = [p for p in (result.get("patients") or [result.get("patient")]) if p]
                    if patients:
                        st.session_state["booking_patients"] = patients
                        st.success(f"Found {len(patients)} record(s)")
                    else:
                        st.warning("No records found.")
                else:
                    st.warning(result.get("message", "Not found."))
            else:
                st.warning("Please enter your name.")

        if st.session_state.get("booking_patients"):
            patients = st.session_state["booking_patients"]
            # Show only name to patient — ID is handled internally
            p_labels = [p.get("Name", p.get("name", "Unknown")) for p in patients]
            p_idx = st.selectbox("Select your record", range(len(p_labels)),
                                  format_func=lambda i: p_labels[i])
            st.session_state["selected_patient"] = patients[p_idx]

            with st.expander("Your Details", expanded=False):
                sp = st.session_state["selected_patient"]
                for k, v in sp.items():
                    # Never display internal ID fields to patient
                    if k not in ["Patient_ID", "patient_id"]:
                        val = str(v).strip()
                        if val and val not in ["", "N/A", "nan", "None"]:
                            st.markdown(f"**{k}:** {val}")

    # Step 2 — Find a doctor by specialty
    with col2:
        st.markdown("**Step 2: Choose a Doctor**")

        spec_result = json.loads(get_all_specialties())
        specialties = spec_result.get("specialties", [])
        book_spec = st.selectbox("Specialty needed", specialties, key="book_spec")
        num_days = st.slider("Days ahead to check", 1, 14, 7)

        if st.button("Find Available Doctors", type="primary"):
            with st.spinner("Finding doctors..."):
                doc_result = json.loads(find_doctors_by_specialty(book_spec))
            if doc_result.get("status") == "success":
                st.session_state["booking_doctors"] = doc_result.get("doctors", [])
                st.success(f"Found {len(st.session_state['booking_doctors'])} doctor(s)")
            else:
                st.warning("No doctors found.")

        if st.session_state.get("booking_doctors"):
            docs = st.session_state["booking_doctors"]
            # Show doctor names and fees — IDs resolved internally
            doc_labels = [
                f"{d['name']} — {d['hospital']} (Rs. {d['consultation_fee']})"
                for d in docs
            ]
            doc_idx = st.selectbox("Select doctor", range(len(doc_labels)),
                                    format_func=lambda i: doc_labels[i])
            st.session_state["selected_doc"] = docs[doc_idx]

            if st.button("Check Available Slots"):
                with st.spinner("Loading slots..."):
                    slots_result = json.loads(get_available_slots_for_doctor(
                        # Resolve doctor_id internally — not shown to patient
                        doctor_id=st.session_state["selected_doc"]["doctor_id"],
                        num_days=num_days
                    ))
                if slots_result.get("status") == "success":
                    st.session_state["booking_slots"] = slots_result.get("slots", [])
                    st.success(f"Found {len(st.session_state['booking_slots'])} available slots")
                else:
                    st.warning("No available slots found.")

    # Step 3 — Confirm booking
    if st.session_state.get("booking_slots") and st.session_state.get("selected_patient"):
        st.divider()
        st.subheader("Step 3: Confirm Your Appointment")

        slots = st.session_state["booking_slots"]
        slot_labels = [
            f"{s['date']} ({s['day']}) at {s['time']} — {s['doctor_name']} @ {s['hospital']}"
            for s in slots
        ]
        slot_idx = st.selectbox("Choose a time slot", range(len(slot_labels)),
                                  format_func=lambda i: slot_labels[i])
        chosen_slot = slots[slot_idx]

        sp = st.session_state["selected_patient"]
        patient_name_display = sp.get("Name", sp.get("name", "Unknown"))
        # Patient ID resolved internally from the record
        patient_id_internal  = str(sp.get("Patient_ID", sp.get("patient_id", "")))

        st.info(
            f"**Patient:** {patient_name_display}  |  "
            f"**Doctor:** {chosen_slot['doctor_name']}  |  "
            f"**Date:** {chosen_slot['date']} at {chosen_slot['time']}"
        )

        if st.button("✅ Confirm Booking", type="primary"):
            with st.spinner("Booking your appointment..."):
                result = json.loads(book_appointment(
                    slot_id=chosen_slot["slot_id"],
                    patient_id=patient_id_internal,
                    patient_name=patient_name_display
                ))
            if result.get("status") == "success":
                details = result.get("booking_details", {})
                st.success("🎉 Appointment Booked Successfully!")
                st.balloons()
                c1, c2, c3 = st.columns(3)
                c1.metric("Doctor",   details.get("doctor_name", ""))
                c2.metric("Date",     details.get("date", ""))
                c3.metric("Time",     details.get("time", ""))
                st.info(f"Hospital: {details.get('hospital', '')} | Specialty: {details.get('specialty', '')}")
                # Clear booking state after successful booking
                for key in ["booking_slots", "booking_patients", "booking_doctors", "selected_patient"]:
                    st.session_state.pop(key, None)
            else:
                st.error(result.get("message", "Booking failed."))

# ── Tab 2: Cancel Appointment ─────────────────────────────────
with tab2:
    st.subheader("Cancel an Appointment")
    st.info("Search by your name to see your appointments, then cancel.")

    cancel_search = st.text_input("Your name", key="cancel_name")

    if st.button("Find My Appointments", key="find_appts_btn"):
        if cancel_search.strip():
            pr = json.loads(get_patient_by_name(cancel_search.strip()))
            if pr.get("status") == "success":
                patients = [p for p in (pr.get("patients") or [pr.get("patient")]) if p]
                if patients:
                    # Resolve patient ID internally
                    pid = str(patients[0].get("Patient_ID", patients[0].get("patient_id", "")))
                    appt_r = json.loads(get_patient_appointments(pid))
                    if appt_r.get("status") == "success":
                        st.session_state["cancel_appointments"] = appt_r.get("appointments", [])
                        st.success(f"Found {len(st.session_state['cancel_appointments'])} appointment(s)")
                    else:
                        st.info("No appointments found.")
            else:
                st.warning("Patient not found.")
        else:
            st.warning("Please enter your name.")

    if st.session_state.get("cancel_appointments"):
        appts = st.session_state["cancel_appointments"]
        appt_labels = [
            f"{a['date']} {a['time']} — {a['doctor_name']} @ {a['hospital']}"
            for a in appts
        ]
        cancel_idx = st.selectbox("Select appointment to cancel",
                                   range(len(appt_labels)),
                                   format_func=lambda i: appt_labels[i])
        chosen = appts[cancel_idx]

        st.warning(
            f"Cancel: **{chosen['doctor_name']}** on "
            f"**{chosen['date']}** at **{chosen['time']}**?"
        )

        if st.button("Confirm Cancellation", type="primary"):
            result = json.loads(cancel_appointment(chosen["slot_id"]))
            if result.get("status") == "success":
                st.success("Appointment cancelled successfully.")
                st.session_state.pop("cancel_appointments", None)
            else:
                st.error(result.get("message", "Cancellation failed."))
