# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/5_Medical_Records.py
# Purpose       : Doctor/Admin Section — Medical Records Management.
#                 Enables attendants to search, view, add, and
#                 update structured and unstructured patient records.
#                 Supports adding new free-text clinical notes
#                 as well as updating existing structured fields.
# =============================================================

import streamlit as st
import json
import sys
import os
import uuid
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from tools.patient_db_tool import (
    get_patient_by_name,
    update_patient_record,
    add_patient_record,
    list_all_patients
)

st.set_page_config(page_title="Medical Records", page_icon="📋", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "admin"
render_sidebar()


# ── Page header ───────────────────────────────────────────────
st.title("📋 Medical Records Management")
st.caption("Doctor / Admin Section — Add and update patient records")
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


tab1, tab2, tab3 = st.tabs(["✏️ Update Record", "➕ Add New Patient", "📂 All Records"])

# ── Tab 1: Update existing record ────────────────────────────
with tab1:
    st.subheader("Update Patient Record")
    st.info("Search for a patient and update any structured or unstructured field.")

    search_name = st.text_input("Search patient by name",
                                 placeholder="e.g. Anjali, David, Ramesh")

    if st.button("Search", key="search_update"):
        if search_name.strip():
            result = json.loads(get_patient_by_name(search_name.strip()))
            if result.get("status") == "success":
                patients = result.get("patients") or [result.get("patient")]
                st.session_state["update_patients"] = [p for p in patients if p]
            else:
                st.warning(result.get("message", "Not found."))
        else:
            st.warning("Please enter a patient name.")

    if st.session_state.get("update_patients"):
        patients = st.session_state["update_patients"]
        p_labels = []
        for p in patients:
            pname = p.get("Name", p.get("name", "Unknown"))
            ppid  = p.get("Patient_ID", "N/A")
            p_labels.append(f"{pname} — ID: {ppid}")

        pidx = st.selectbox("Select patient", range(len(p_labels)),
                              format_func=lambda i: p_labels[i])
        selected_p = patients[pidx]
        # Resolve Patient_ID using the canonical column name
        pid = str(selected_p.get("Patient_ID", ""))

        st.markdown("**Current Record:**")
        st.dataframe(safe_df([selected_p]), width='stretch')

        st.divider()
        st.markdown("**Update a Field:**")

        update_mode = st.radio(
            "Update mode",
            ["Update existing field", "Add new unstructured note"],
            horizontal=True
        )

        if update_mode == "Update existing field":
            # Exclude the primary key from editable fields
            existing_fields = [k for k in selected_p.keys() if k != "Patient_ID"]
            field_to_update = st.selectbox("Select field to update", existing_fields)
            current_val = str(selected_p.get(field_to_update, ""))
            st.caption(f"Current value: {current_val}")
            new_value = st.text_area("New value", value=current_val, height=100)
        else:
            # Free-text unstructured field — attendant defines field name
            field_to_update = st.text_input(
                "New field name",
                placeholder="e.g. Clinical_Notes, Allergy_History, Last_Procedure"
            )
            new_value = st.text_area(
                "Field content",
                placeholder="Enter unstructured notes, clinical observations, etc.",
                height=150
            )

        if st.button("💾 Save Update", type="primary", key="save_update"):
            if field_to_update and new_value:
                with st.spinner("Saving..."):
                    result = json.loads(update_patient_record(pid, field_to_update, new_value))
                if result.get("status") == "success":
                    st.success(f"✅ {result.get('message', 'Record updated.')}")
                    st.session_state["update_patients"] = []
                else:
                    st.error(result.get("message", "Update failed."))
            else:
                st.warning("Please fill in both field name and value.")

# ── Tab 2: Add new patient ────────────────────────────────────
with tab2:
    st.subheader("Add New Patient Record")
    st.info("Fill in patient details to register a new patient. Patient_ID is auto-generated.")

    st.markdown("**Basic Information**")
    c1, c2 = st.columns(2)
    with c1:
        new_name        = st.text_input("Full Name *")
        new_dob         = st.text_input("Date of Birth", placeholder="DD/MM/YYYY")
        new_gender      = st.selectbox("Gender", ["", "Male", "Female", "Other"])
        new_phone       = st.text_input("Phone Number", placeholder="+91-XXXXX-XXXXX")
    with c2:
        new_email       = st.text_input("Email")
        new_address     = st.text_area("Address", height=100)
        new_blood_group = st.selectbox("Blood Group",
                                        ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

    st.markdown("**Medical Information**")
    c3, c4 = st.columns(2)
    with c3:
        new_diagnosis   = st.text_input("Current Diagnosis", placeholder="e.g. Type 2 Diabetes")
        new_medications = st.text_input("Current Medications", placeholder="e.g. Metformin 500mg")
        new_allergies   = st.text_input("Known Allergies", placeholder="e.g. Penicillin")
    with c4:
        new_bp          = st.text_input("Blood Pressure", placeholder="e.g. 120/80")
        new_weight      = st.text_input("Weight (kg)")
        new_height      = st.text_input("Height (cm)")

    new_notes = st.text_area(
        "Clinical Notes (unstructured)",
        placeholder="Any additional clinical observations, history, or free-text notes...",
        height=120
    )

    if st.button("➕ Add Patient", type="primary"):
        if not new_name.strip():
            st.error("Patient name is required.")
        else:
            # Build patient data dict — skip empty fields
            all_fields = {
                "Name": new_name, "DOB": new_dob, "Gender": new_gender,
                "Phone_number": new_phone, "Email": new_email,
                "Address": new_address, "Blood_Group": new_blood_group,
                "Diagnosis": new_diagnosis, "Medications": new_medications,
                "Allergies": new_allergies, "BP": new_bp,
                "Weight_kg": new_weight, "Height_cm": new_height,
                "Clinical_Notes": new_notes
            }
            patient_data = {k: v for k, v in all_fields.items() if str(v).strip()}

            with st.spinner("Adding patient..."):
                result = json.loads(add_patient_record(patient_data))
            if result.get("status") == "success":
                assigned_id = result.get("patient", {}).get("Patient_ID", "")
                st.success(f"✅ Patient added! Assigned ID: **{assigned_id}**")
                st.json(result.get("patient", {}))
            else:
                st.error(result.get("message", "Failed to add patient."))

# ── Tab 3: View all records ───────────────────────────────────
with tab3:
    st.subheader("All Patient Records")
    if st.button("📂 Load All Records", type="primary"):
        with st.spinner("Loading..."):
            result = json.loads(list_all_patients())
        if result.get("status") == "success":
            patients = result.get("patients", [])
            st.success(f"Total records: {len(patients)}")
            st.dataframe(safe_df(patients), width='stretch')
        else:
            st.error("Failed to load records.")
