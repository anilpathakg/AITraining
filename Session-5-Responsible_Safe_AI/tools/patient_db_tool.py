# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : tools/patient_db_tool.py
# Purpose       : Patient database access layer.
#                 Provides CRUD operations on records.xlsx —
#                 the structured patient records store.
#                 Used by both the agent (via function calling)
#                 and the Streamlit UI pages directly.
# =============================================================

import pandas as pd
import json
import os
from typing import Optional

# Use central config for consistent path resolution
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RECORDS_FILE

# ── Column name resolution ───────────────────────────────────
# Priority order for ID and Name column detection.
# 'Patient_ID' is the canonical name used in this project.
ID_COLUMN_CANDIDATES   = ["Patient_ID", "patient_id", "PatientID", "Patient ID", "ID", "id"]
NAME_COLUMN_CANDIDATES = ["Name", "name", "Patient Name", "patient_name", "PatientName"]


# ── Internal helpers ─────────────────────────────────────────

def _load_patients() -> pd.DataFrame:
    """
    Load the patient records Excel file into a DataFrame.

    Returns:
        pd.DataFrame: Patient records with cleaned column names.

    Raises:
        FileNotFoundError: If records.xlsx is not found at configured path.
    """
    if not os.path.exists(RECORDS_FILE):
        raise FileNotFoundError(f"records.xlsx not found at: {RECORDS_FILE}")
    df = pd.read_excel(RECORDS_FILE)
    # Strip whitespace from column names to avoid subtle mismatches
    df.columns = [str(c).strip() for c in df.columns]
    # Always keep phone numbers as strings to prevent Arrow serialisation errors
    for col in df.columns:
        if "phone" in col.lower():
            df[col] = df[col].astype(str)
    return df


def _find_id_column(df: pd.DataFrame) -> Optional[str]:
    """
    Locate the patient ID column using a priority candidate list.

    Args:
        df (pd.DataFrame): The loaded patient records DataFrame.

    Returns:
        str | None: The matched column name, or None if not found.
    """
    for candidate in ID_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate
    # Broad fallback: any column containing 'id'
    for col in df.columns:
        if "id" in col.lower():
            return col
    return None


def _find_name_column(df: pd.DataFrame) -> Optional[str]:
    """
    Locate the patient name column using a priority candidate list.

    Args:
        df (pd.DataFrame): The loaded patient records DataFrame.

    Returns:
        str | None: The matched column name, or None if not found.
    """
    for candidate in NAME_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate
    for col in df.columns:
        if "name" in col.lower():
            return col
    return None


# ── Public tool functions ────────────────────────────────────

def get_patient_by_name(name: str) -> str:
    """
    Search for patients by name (partial, case-insensitive match).

    Args:
        name (str): Full or partial patient name to search for.

    Returns:
        str: JSON string with status, count, and matching patient records.

    Example:
        result = get_patient_by_name("Anjali")
    """
    try:
        df = _load_patients()
        name_col = _find_name_column(df)
        if not name_col:
            return json.dumps({"status": "error", "message": "No name column found in records."})

        mask = df[name_col].astype(str).str.lower().str.contains(name.lower(), na=False)
        result = df[mask]

        if result.empty:
            return json.dumps({
                "status": "not_found",
                "message": f"No patient found with name containing '{name}'",
                "patients": []
            })

        patients = result.fillna("N/A").to_dict(orient="records")
        return json.dumps({"status": "success", "count": len(patients), "patients": patients}, default=str)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def get_patient_by_id(patient_id: str) -> str:
    """
    Retrieve a single patient record by their unique Patient_ID.

    Args:
        patient_id (str): The patient's unique ID (e.g. 'P001').

    Returns:
        str: JSON string with status and patient record dict.

    Example:
        result = get_patient_by_id("P001")
    """
    try:
        df = _load_patients()
        id_col = _find_id_column(df)
        if not id_col:
            return json.dumps({"status": "error", "message": "No ID column found in records."})

        # Case-insensitive exact match on ID
        mask = df[id_col].astype(str).str.strip().str.lower() == str(patient_id).strip().lower()
        result = df[mask]

        if result.empty:
            return json.dumps({"status": "not_found", "message": f"No patient found with ID '{patient_id}'"})

        patient = result.fillna("N/A").iloc[0].to_dict()
        return json.dumps({"status": "success", "patient": patient}, default=str)

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def list_all_patients() -> str:
    """
    Return all patient records as a list.

    Returns:
        str: JSON string with status, total count, and all patient records.

    Example:
        result = list_all_patients()
    """
    try:
        df = _load_patients()
        patients = df.fillna("N/A").to_dict(orient="records")
        return json.dumps({"status": "success", "total_patients": len(patients), "patients": patients}, default=str)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def update_patient_record(patient_id: str, field: str, value: str) -> str:
    """
    Update a specific field for a patient identified by Patient_ID.
    If the field does not exist, it is added as a new column (supports
    unstructured free-text fields like Clinical_Notes).

    Args:
        patient_id (str): The patient's unique ID (e.g. 'P001').
        field      (str): Column name to update or create.
        value      (str): New value to set.

    Returns:
        str: JSON string with status and confirmation message.

    Example:
        result = update_patient_record("P001", "Diagnosis", "Type 2 Diabetes")
    """
    try:
        df = _load_patients()
        id_col = _find_id_column(df)

        if not id_col:
            return json.dumps({
                "status": "error",
                "message": f"No ID column found. Available columns: {list(df.columns)}"
            })

        mask = df[id_col].astype(str).str.strip().str.lower() == str(patient_id).strip().lower()
        if not mask.any():
            return json.dumps({
                "status": "not_found",
                "message": f"Patient ID '{patient_id}' not found. Available IDs: {df[id_col].tolist()}"
            })

        # Find best matching column — exact match first, then partial
        field_col = None
        for col in df.columns:
            if field.lower() == col.lower():
                field_col = col
                break
        if not field_col:
            for col in df.columns:
                if field.lower() in col.lower():
                    field_col = col
                    break

        # If no matching column, create a new one (unstructured field support)
        if not field_col:
            df[field] = ""
            field_col = field

        df.loc[mask, field_col] = value
        df.to_excel(RECORDS_FILE, index=False)

        return json.dumps({
            "status": "success",
            "message": f"Updated '{field_col}' for patient '{patient_id}' → '{value}'"
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def add_patient_record(patient_data: dict) -> str:
    """
    Add a new patient record to records.xlsx.
    Auto-generates a Patient_ID if not provided.

    Args:
        patient_data (dict): Dictionary of field names and values
                             for the new patient.

    Returns:
        str: JSON string with status and the saved patient data.

    Example:
        result = add_patient_record({"Name": "John Doe", "Age": "45"})
    """
    try:
        df = _load_patients()

        # Auto-generate next sequential Patient_ID if not provided
        if "Patient_ID" not in patient_data:
            id_col = _find_id_column(df)
            if id_col:
                nums = []
                for eid in df[id_col].astype(str).tolist():
                    try:
                        nums.append(int(eid.replace("P", "").replace("p", "")))
                    except Exception:
                        pass
                next_num = max(nums) + 1 if nums else 1
                patient_data["Patient_ID"] = f"P{next_num:03d}"

        new_row = pd.DataFrame([patient_data])
        df = pd.concat([df, new_row], ignore_index=True)

        # Keep phone numbers as strings after concat
        for col in df.columns:
            if "phone" in col.lower():
                df[col] = df[col].astype(str)

        df.to_excel(RECORDS_FILE, index=False)
        return json.dumps({"status": "success", "message": "Patient added successfully.", "patient": patient_data})

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
