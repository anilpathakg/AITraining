# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : config.py
# Purpose       : Central configuration and path management.
#                 Single source of truth for all file paths
#                 used across the application. Ensures correct
#                 path resolution regardless of working directory
#                 when running under Streamlit.
# =============================================================

import os

# Absolute path to the project root (directory where this file lives)
# Using __file__ ensures paths resolve correctly from any CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Directory paths ──────────────────────────────────────────
DATA_DIR         = os.path.join(BASE_DIR, "data")
REPORTS_DIR      = os.path.join(DATA_DIR, "reports")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "vector_store", "patient_reports")

# ── File paths ───────────────────────────────────────────────
LOG_FILE     = os.path.join(DATA_DIR, "interaction_logs.json")
RECORDS_FILE = os.path.join(DATA_DIR, "records.xlsx")
DOCTORS_FILE = os.path.join(DATA_DIR, "doctors.xlsx")

# ── Ensure data directory exists on first import ─────────────
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
