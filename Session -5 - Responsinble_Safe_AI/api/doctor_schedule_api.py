# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : api/doctor_schedule_api.py
# Purpose       : Mock Doctor Schedule API.
#                 Simulates a real hospital scheduling backend
#                 using doctors.xlsx as the data store.
#                 Provides endpoints for doctor lookup, slot
#                 availability, booking, cancellation, and
#                 schedule retrieval. Designed to be swappable
#                 with a real REST API in production.
# =============================================================

import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DOCTORS_FILE


class DoctorScheduleAPI:
    """
    Mock implementation of a Doctor Schedule API.

    Reads doctor master data from doctors.xlsx and manages
    appointment slots in memory. In production this class would
    be replaced by HTTP calls to a real scheduling service.

    Attributes:
        _doctors  (pd.DataFrame): Loaded doctor records.
        _slots    (dict):         In-memory slot store keyed by slot_id.
        _bookings (dict):         In-memory booking store keyed by slot_id.
    """

    def __init__(self):
        """
        Initialise the API by loading doctors.xlsx and generating
        appointment slots for the next 30 days.
        """
        self._doctors  = self._load_doctors()
        self._slots    = {}
        self._bookings = {}
        self._generate_slots(days_ahead=30)

    # ── Data loading ──────────────────────────────────────────

    def _load_doctors(self) -> pd.DataFrame:
        """
        Load doctor master data from doctors.xlsx.

        Returns:
            pd.DataFrame: Doctor records, or empty DataFrame if file missing.
        """
        if not os.path.exists(DOCTORS_FILE):
            print(f"⚠️  doctors.xlsx not found at {DOCTORS_FILE}. Run setup_data.py first.")
            return pd.DataFrame()
        df = pd.read_excel(DOCTORS_FILE)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def _generate_slots(self, days_ahead: int = 30):
        """
        Pre-generate hourly appointment slots for all doctors
        for the next `days_ahead` days (Mon–Sat, 9 AM–5 PM).

        Each slot is assigned a unique slot_id (e.g. S0001) and
        stored in the in-memory _slots dictionary with status 'available'.

        Args:
            days_ahead (int): Number of days ahead to generate slots for.
        """
        if self._doctors.empty:
            return

        slot_counter = 1
        today        = datetime.now().date()
        work_hours   = range(9, 17)   # 9 AM to 4 PM (last slot at 4 PM)

        for day_offset in range(days_ahead):
            date = today + timedelta(days=day_offset)
            # Skip Sundays (weekday 6)
            if date.weekday() == 6:
                continue

            for _, doctor in self._doctors.iterrows():
                for hour in work_hours:
                    slot_id = f"S{slot_counter:04d}"
                    self._slots[slot_id] = {
                        "slot_id":     slot_id,
                        "doctor_id":   str(doctor.get("doctor_id", "")),
                        "doctor_name": str(doctor.get("name", "")),
                        "specialty":   str(doctor.get("specialty", "")),
                        "hospital":    str(doctor.get("hospital", "")),
                        "date":        date.strftime("%Y-%m-%d"),
                        "day":         date.strftime("%A"),
                        "time":        f"{hour:02d}:00",
                        "status":      "available",
                        "patient_id":  None,
                        "patient_name":None
                    }
                    slot_counter += 1

    # ── Public API methods ────────────────────────────────────

    def get_specialties(self) -> dict:
        """
        Return all unique medical specialties available in the system.

        Returns:
            dict: Status and list of specialty names.
        """
        if self._doctors.empty:
            return {"status": "error", "message": "No doctor data available."}
        specialties = sorted(self._doctors["specialty"].dropna().unique().tolist())
        return {"status": "success", "specialties": specialties}

    def get_doctors_by_specialty(self, specialty: str) -> dict:
        """
        Find all doctors matching a given specialty (case-insensitive).

        Args:
            specialty (str): Medical specialty to search for.

        Returns:
            dict: Status and list of matching doctor profiles.
        """
        if self._doctors.empty:
            return {"status": "error", "message": "No doctor data available."}

        mask    = self._doctors["specialty"].str.lower() == specialty.lower()
        matches = self._doctors[mask]

        if matches.empty:
            return {
                "status":  "not_found",
                "message": f"No doctors found for specialty: {specialty}"
            }

        doctors = matches.fillna("N/A").to_dict(orient="records")
        return {"status": "success", "specialty": specialty, "doctors": doctors}

    def get_available_slots(self, doctor_id: str,
                             from_date: Optional[str] = None,
                             max_days: int = 7) -> dict:
        """
        Get available appointment slots for a specific doctor.

        Args:
            doctor_id (str):          The doctor's internal ID.
            from_date (str, optional):Start date (YYYY-MM-DD). Defaults to today.
            max_days  (int):          Number of days to look ahead. Default 7.

        Returns:
            dict: Status and list of available slot details.
        """
        try:
            start = (
                datetime.strptime(from_date, "%Y-%m-%d").date()
                if from_date else datetime.now().date()
            )
            end = start + timedelta(days=max_days)
        except ValueError:
            start = datetime.now().date()
            end   = start + timedelta(days=max_days)

        available = [
            s for s in self._slots.values()
            if (s["doctor_id"] == doctor_id
                and s["status"] == "available"
                and start <= datetime.strptime(s["date"], "%Y-%m-%d").date() < end)
        ]

        if not available:
            return {
                "status":  "no_slots",
                "message": f"No available slots for doctor {doctor_id} in this period."
            }

        # Sort chronologically
        available.sort(key=lambda x: (x["date"], x["time"]))
        return {"status": "success", "doctor_id": doctor_id, "slots": available}

    def book_slot(self, slot_id: str, patient_id: str,
                  patient_name: str) -> dict:
        """
        Book a specific available slot for a patient.

        Args:
            slot_id      (str): The slot ID to book (e.g. 'S0042').
            patient_id   (str): The patient's unique ID.
            patient_name (str): The patient's full name.

        Returns:
            dict: Status, confirmation message, and booking details.
        """
        slot_id = slot_id.upper().strip()

        if slot_id not in self._slots:
            return {"status": "error", "message": f"Slot {slot_id} does not exist."}

        slot = self._slots[slot_id]
        if slot["status"] != "available":
            return {
                "status":  "unavailable",
                "message": f"Slot {slot_id} is already booked."
            }

        # Mark slot as booked and record patient details
        self._slots[slot_id]["status"]       = "booked"
        self._slots[slot_id]["patient_id"]   = patient_id
        self._slots[slot_id]["patient_name"] = patient_name

        booking_details = {
            "slot_id":      slot_id,
            "patient_id":   patient_id,
            "patient_name": patient_name,
            "doctor_name":  slot["doctor_name"],
            "specialty":    slot["specialty"],
            "hospital":     slot["hospital"],
            "date":         slot["date"],
            "day":          slot["day"],
            "time":         slot["time"],
            "booked_at":    datetime.now().isoformat()
        }
        self._bookings[slot_id] = booking_details

        return {
            "status":          "success",
            "message":         f"Appointment booked successfully for {patient_name}.",
            "booking_details": booking_details
        }

    def cancel_appointment(self, slot_id: str) -> dict:
        """
        Cancel a booked appointment and make the slot available again.

        Args:
            slot_id (str): The slot ID to cancel.

        Returns:
            dict: Status and cancellation confirmation message.
        """
        slot_id = slot_id.upper().strip()

        if slot_id not in self._slots:
            return {"status": "error", "message": f"Slot {slot_id} does not exist."}

        slot = self._slots[slot_id]
        if slot["status"] != "booked":
            return {"status": "error", "message": f"Slot {slot_id} is not currently booked."}

        patient_name = slot.get("patient_name", "Unknown")

        # Reset slot to available state
        self._slots[slot_id]["status"]       = "available"
        self._slots[slot_id]["patient_id"]   = None
        self._slots[slot_id]["patient_name"] = None

        # Remove from bookings store
        self._bookings.pop(slot_id, None)

        return {
            "status":  "success",
            "message": f"Appointment cancelled for {patient_name} (Slot: {slot_id})."
        }

    def get_patient_appointments(self, patient_id: str) -> dict:
        """
        Retrieve all booked appointments for a specific patient.

        Args:
            patient_id (str): The patient's unique ID.

        Returns:
            dict: Status and list of booked appointment details.
        """
        appointments = [
            s for s in self._slots.values()
            if s["status"] == "booked" and s.get("patient_id") == patient_id
        ]

        if not appointments:
            return {
                "status":       "success",
                "message":      f"No appointments found for patient {patient_id}.",
                "appointments": []
            }

        appointments.sort(key=lambda x: (x["date"], x["time"]))
        return {
            "status":       "success",
            "patient_id":   patient_id,
            "appointments": appointments
        }

    def get_doctor_schedule(self, doctor_id: str,
                             from_date: Optional[str] = None,
                             max_days: int = 7) -> dict:
        """
        Retrieve the full schedule for a doctor — both available and
        booked slots — for display on the Doctor Schedule page.

        Args:
            doctor_id (str):          The doctor's internal ID.
            from_date (str, optional):Start date (YYYY-MM-DD). Defaults to today.
            max_days  (int):          Number of days to include. Default 7.

        Returns:
            dict: Status and complete schedule (all slot statuses).
        """
        try:
            start = (
                datetime.strptime(from_date, "%Y-%m-%d").date()
                if from_date else datetime.now().date()
            )
            end = start + timedelta(days=max_days)
        except ValueError:
            start = datetime.now().date()
            end   = start + timedelta(days=max_days)

        schedule = [
            s for s in self._slots.values()
            if (s["doctor_id"] == doctor_id
                and start <= datetime.strptime(s["date"], "%Y-%m-%d").date() < end)
        ]
        schedule.sort(key=lambda x: (x["date"], x["time"]))

        return {
            "status":    "success",
            "doctor_id": doctor_id,
            "schedule":  schedule,
            "total":     len(schedule),
            "booked":    sum(1 for s in schedule if s["status"] == "booked"),
            "available": sum(1 for s in schedule if s["status"] == "available")
        }
