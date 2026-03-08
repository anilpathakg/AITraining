"""
Run this script ONCE to generate doctors.xlsx with
doctor profiles and daily appointment slots for the next 30 days.
"""

import pandas as pd
from datetime import datetime, timedelta
import os

def generate_doctors_data():
    doctors = [
        {
            "doctor_id": "D001",
            "name": "Dr. Priya Sharma",
            "specialty": "General Physician",
            "qualification": "MBBS, MD (Internal Medicine)",
            "hospital": "Apollo Clinic, Pune",
            "phone": "+91-98100-11001",
            "email": "priya.sharma@apolloclinic.com",
            "experience_years": 12,
            "consultation_fee": 500
        },
        {
            "doctor_id": "D002",
            "name": "Dr. Arun Mehta",
            "specialty": "Cardiologist",
            "qualification": "MBBS, MD, DM (Cardiology)",
            "hospital": "Fortis Hospital, Bangalore",
            "phone": "+91-98100-22002",
            "email": "arun.mehta@fortis.com",
            "experience_years": 18,
            "consultation_fee": 1200
        },
        {
            "doctor_id": "D003",
            "name": "Dr. Sunita Rao",
            "specialty": "Nephrologist",
            "qualification": "MBBS, MD, DM (Nephrology)",
            "hospital": "Manipal Hospital, Chennai",
            "phone": "+91-98100-33003",
            "email": "sunita.rao@manipal.com",
            "experience_years": 15,
            "consultation_fee": 1500
        },
        {
            "doctor_id": "D004",
            "name": "Dr. Vikram Nair",
            "specialty": "Diabetologist",
            "qualification": "MBBS, MD, Fellowship (Endocrinology)",
            "hospital": "Max Healthcare, Delhi",
            "phone": "+91-98100-44004",
            "email": "vikram.nair@maxhealthcare.com",
            "experience_years": 10,
            "consultation_fee": 800
        },
        {
            "doctor_id": "D005",
            "name": "Dr. Kavita Joshi",
            "specialty": "General Physician",
            "qualification": "MBBS, MD (Family Medicine)",
            "hospital": "City Clinic, Mumbai",
            "phone": "+91-98100-55005",
            "email": "kavita.joshi@cityclinic.com",
            "experience_years": 8,
            "consultation_fee": 450
        },
        {
            "doctor_id": "D006",
            "name": "Dr. Rajesh Patel",
            "specialty": "Cardiologist",
            "qualification": "MBBS, MD, DM (Cardiology)",
            "hospital": "Kokilaben Hospital, Mumbai",
            "phone": "+91-98100-66006",
            "email": "rajesh.patel@kokilaben.com",
            "experience_years": 20,
            "consultation_fee": 1800
        },
        {
            "doctor_id": "D007",
            "name": "Dr. Meena Krishnan",
            "specialty": "Nephrologist",
            "qualification": "MBBS, MD, DM (Nephrology)",
            "hospital": "AIMS Hospital, Kochi",
            "phone": "+91-98100-77007",
            "email": "meena.krishnan@aims.com",
            "experience_years": 14,
            "consultation_fee": 1400
        },
        {
            "doctor_id": "D008",
            "name": "Dr. Suresh Bhat",
            "specialty": "Diabetologist",
            "qualification": "MBBS, MD (Endocrinology)",
            "hospital": "Narayana Health, Bangalore",
            "phone": "+91-98100-88008",
            "email": "suresh.bhat@narayana.com",
            "experience_years": 16,
            "consultation_fee": 900
        },
    ]

    # Generate slots for next 30 days
    # Mon-Sat working days, 9AM-12PM and 2PM-5PM, hourly slots
    time_slots = [
        "09:00 AM", "10:00 AM", "11:00 AM",
        "02:00 PM", "03:00 PM", "04:00 PM"
    ]

    slots = []
    slot_counter = 1
    start_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        # Skip Sundays (weekday 6)
        if current_date.weekday() == 6:
            continue

        for doctor in doctors:
            for time_slot in time_slots:
                slots.append({
                    "slot_id": f"S{slot_counter:04d}",
                    "doctor_id": doctor["doctor_id"],
                    "doctor_name": doctor["name"],
                    "specialty": doctor["specialty"],
                    "hospital": doctor["hospital"],
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day": current_date.strftime("%A"),
                    "time": time_slot,
                    "is_booked": False,
                    "patient_id": "",
                    "patient_name": "",
                    "booked_on": ""
                })
                slot_counter += 1

    doctors_df = pd.DataFrame(doctors)
    slots_df = pd.DataFrame(slots)

    os.makedirs("data", exist_ok=True)
    output_path = "data/doctors.xlsx"

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        doctors_df.to_excel(writer, sheet_name="Doctors", index=False)
        slots_df.to_excel(writer, sheet_name="Slots", index=False)

    print(f"✅ doctors.xlsx created at: {output_path}")
    print(f"   → {len(doctors)} doctors added")
    print(f"   → {len(slots)} appointment slots generated (next 30 days)")
    print(f"\nDoctors added:")
    for d in doctors:
        print(f"  [{d['doctor_id']}] {d['name']} — {d['specialty']} @ {d['hospital']}")


if __name__ == "__main__":
    generate_doctors_data()python setup_data.py
    