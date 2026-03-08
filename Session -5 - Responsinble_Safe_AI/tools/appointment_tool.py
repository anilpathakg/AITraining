# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : tools/appointment_tool.py
# Purpose       : Appointment management tool layer.
#                 Wraps DoctorScheduleAPI for use by both the
#                 agent (via function calling) and Streamlit UI.
#                 Logs all booking attempts directly so that
#                 booking success rate metrics are captured
#                 regardless of call origin (agent or UI).
# =============================================================

import json
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.doctor_schedule_api import DoctorScheduleAPI

# Single shared API instance
_api = DoctorScheduleAPI()


# ── Internal helper ──────────────────────────────────────────

def _log(tool_name: str, tool_args: dict, tool_result: str,
         success: bool, elapsed_ms: float):
    """
    Log a tool call to the interaction log via the logger module.
    Uses session_id='ui_direct' for calls originating from the UI
    (as opposed to agent-originated calls which use a session ID).

    Args:
        tool_name  (str):   Name of the tool called.
        tool_args  (dict):  Arguments passed to the tool.
        tool_result(str):   JSON string result from the tool.
        success    (bool):  Whether the call succeeded.
        elapsed_ms (float): Execution time in milliseconds.
    """
    try:
        from evaluation.logger import log_tool_call
        log_tool_call(
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            success=success,
            execution_time_ms=elapsed_ms,
            session_id="ui_direct"
        )
    except Exception:
        pass  # Logging failure must never break the main flow


# ── Public tool functions ────────────────────────────────────

def find_doctors_by_specialty(specialty: str) -> str:
    """
    Find all doctors matching a given medical specialty.

    Args:
        specialty (str): Medical specialty name
                         (e.g. 'Cardiologist', 'General Physician').

    Returns:
        str: JSON string with list of matching doctors and their details.

    Example:
        result = find_doctors_by_specialty("Cardiologist")
    """
    start = time.time()
    result = _api.get_doctors_by_specialty(specialty)
    output = json.dumps(result, default=str)
    _log("find_doctors_by_specialty", {"specialty": specialty},
         output, result.get("status") == "success", (time.time() - start) * 1000)
    return output


def get_available_slots_for_doctor(doctor_id: str,
                                    from_date: str = "",
                                    num_days: int = 7) -> str:
    """
    Retrieve available appointment slots for a specific doctor.

    Args:
        doctor_id (str): The doctor's internal ID (e.g. 'D001').
        from_date (str): Start date in YYYY-MM-DD format.
                         Defaults to today if empty.
        num_days  (int): Number of days ahead to check. Default 7.

    Returns:
        str: JSON string with list of available time slots.

    Example:
        result = get_available_slots_for_doctor("D001", num_days=5)
    """
    start = time.time()
    result = _api.get_available_slots(
        doctor_id=doctor_id,
        from_date=from_date if from_date else None,
        max_days=num_days
    )
    output = json.dumps(result, default=str)
    _log("get_available_slots_for_doctor",
         {"doctor_id": doctor_id, "num_days": num_days},
         output, result.get("status") == "success", (time.time() - start) * 1000)
    return output


def book_appointment(slot_id: str, patient_id: str,
                     patient_name: str) -> str:
    """
    Book a specific appointment slot for a patient.

    Booking attempts are always logged directly in this function
    so that success rate metrics are captured whether the call
    comes from the agent or the Doctor View UI page.

    Args:
        slot_id      (str): The slot ID to book (e.g. 'S0042').
        patient_id   (str): The patient's unique ID (e.g. 'P001').
        patient_name (str): The patient's full name.

    Returns:
        str: JSON string with booking confirmation and details.

    Example:
        result = book_appointment("S0042", "P001", "Anjali Mehra")
    """
    start = time.time()
    result = _api.book_slot(
        slot_id=slot_id,
        patient_id=patient_id,
        patient_name=patient_name
    )
    output = json.dumps(result, default=str)
    success = result.get("status") == "success"
    elapsed = (time.time() - start) * 1000

    # Always log booking — critical for booking success rate KPI
    _log("book_appointment",
         {"slot_id": slot_id, "patient_id": patient_id, "patient_name": patient_name},
         output, success, elapsed)
    return output


def cancel_appointment(slot_id: str) -> str:
    """
    Cancel an existing booked appointment by slot ID.

    Args:
        slot_id (str): The slot ID to cancel (e.g. 'S0042').

    Returns:
        str: JSON string with cancellation status and message.

    Example:
        result = cancel_appointment("S0042")
    """
    start = time.time()
    result = _api.cancel_appointment(slot_id)
    output = json.dumps(result, default=str)
    _log("cancel_appointment", {"slot_id": slot_id},
         output, result.get("status") == "success", (time.time() - start) * 1000)
    return output


def get_patient_appointments(patient_id: str) -> str:
    """
    Retrieve all booked appointments for a given patient.

    Args:
        patient_id (str): The patient's unique ID (e.g. 'P001').

    Returns:
        str: JSON string with list of booked appointments.

    Example:
        result = get_patient_appointments("P001")
    """
    result = _api.get_patient_appointments(patient_id)
    return json.dumps(result, default=str)


def get_all_specialties() -> str:
    """
    Return all available medical specialties in the system.

    Returns:
        str: JSON string with list of specialty names.

    Example:
        result = get_all_specialties()
    """
    result = _api.get_specialties()
    return json.dumps(result, default=str)


def get_doctor_schedule(doctor_id: str) -> str:
    """
    Retrieve the full appointment schedule for a specific doctor,
    including both booked and available slots.

    Args:
        doctor_id (str): The doctor's internal ID (e.g. 'D001').

    Returns:
        str: JSON string with the doctor's complete schedule.

    Example:
        result = get_doctor_schedule("D001")
    """
    result = _api.get_doctor_schedule(doctor_id)
    return json.dumps(result, default=str)
