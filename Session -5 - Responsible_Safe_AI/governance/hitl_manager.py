# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# File    : governance/hitl_manager.py
# Author  : Anil Pathak
# Purpose : Implements Pillar 5 — Human-in-the-Loop (HITL).
#
# ══════════════════════════════════════════════════════════════
# GOVERNANCE PILLAR 5 — HUMAN-IN-THE-LOOP (HITL)
# ══════════════════════════════════════════════════════════════
#
# WHY THIS EXISTS:
#   Autonomous agents should NOT be allowed to make irreversible
#   or high-impact decisions without human oversight.
#   In a healthcare context, actions like:
#     • Updating a patient's diagnosis or medications
#     • Cancelling an appointment
#     • Modifying critical patient records
#   ...should always require explicit human approval.
#
#   This is the "human in the loop" pattern — the agent PAUSES
#   before executing a high-risk tool, and waits for a human
#   to Approve, Reject, or Edit the proposed action.
#
# ARCHITECTURE (where this sits):
#
#   agent.chat()
#       ↓
#   Tool call decided by LLM
#       ↓
#   [classify_risk(tool_name, tool_args)]  ← THIS FILE
#       ↓ HIGH RISK
#   Store pending action in st.session_state
#   RAISE HITLInterrupt (execution paused)
#       ↓
#   Streamlit UI shows Approve / Reject / Edit widget
#       ↓
#   User makes decision → action logged → agent resumes or aborts
#
# IMPLEMENTATION APPROACH — OPTION A (Streamlit session_state):
#   We use Streamlit's session_state as the "interrupt" mechanism
#   rather than LangGraph's interrupt() node.  This approach:
#     • Keeps the codebase simpler for teaching purposes
#     • Works natively with the existing agent.py loop
#     • Is equally effective at enforcing human approval
#
#   Option B (LangGraph interrupt) is covered conceptually in
#   the Session 5 slides — showing the architectural diagram of
#   how a LangGraph checkpoint would work.  This implementation
#   (Option A) is the working demo code.
#
# RISK CLASSIFICATION:
#   HIGH   → Tools that WRITE/MODIFY/DELETE data
#              (update_patient_record, cancel_appointment,
#               book_appointment, add_patient_record)
#   LOW    → Tools that READ-ONLY
#              (all search, lookup, retrieval tools)
#
# TEACHING NOTE FOR STUDENTS:
#   The HITL pattern is one of the most important safety
#   mechanisms in responsible AI.  It embodies the principle
#   that AI should *assist* humans, not *replace* human
#   judgement on consequential decisions.
#   LangGraph's interrupt() provides a more robust graph-based
#   approach — this implementation demonstrates the same concept
#   using simpler Streamlit state management.
# ══════════════════════════════════════════════════════════════


# ── Risk classification table ─────────────────────────────────
# Maps tool names to their risk level.
# HIGH  → requires human approval before execution
# LOW   → executes automatically (no approval needed)
#
# NOTE: book_appointment is marked HIGH because booking the wrong
# appointment for a patient has real clinical consequences.

TOOL_RISK_LEVELS = {
    # ── HIGH RISK: write/modify/delete operations ────────────
    "update_patient_record": "HIGH",
    "cancel_appointment":    "HIGH",
    "book_appointment":      "HIGH",
    "add_patient_record":    "HIGH",

    # ── LOW RISK: read-only operations ───────────────────────
    "find_doctors_by_specialty":      "LOW",
    "get_available_slots_for_doctor": "LOW",
    "get_patient_appointments":       "LOW",
    "get_patient_by_name":            "LOW",
    "get_patient_by_id":              "LOW",
    "list_all_patients":              "LOW",
    "retrieve_patient_history":       "LOW",
    "search_medical_information":     "LOW",
    "get_disease_overview":           "LOW",
    "get_drug_information":           "LOW",
    "search_across_all_patients":     "LOW",
}

# ── Human-readable descriptions for the approval widget ───────
# Shown in the HITL widget so the approver understands the action.

TOOL_DESCRIPTIONS = {
    "update_patient_record": "Update a field in a patient's medical record",
    "cancel_appointment":    "Cancel an existing appointment",
    "book_appointment":      "Book an appointment for a patient",
    "add_patient_record":    "Add a new patient to the system",
}


class HITLInterrupt(Exception):
    """
    Custom exception raised when a HIGH RISK tool call is intercepted.

    PILLAR 5 — HUMAN-IN-THE-LOOP

    Raising this exception causes the agent's dispatch_tool()
    call to be interrupted.  The pending action details are stored
    in st.session_state["hitl_pending"] by the caller (agent.py)
    before raising this exception.

    The Streamlit chat page catches this exception and renders
    the Approve / Reject / Edit widget instead of the normal
    agent response.

    Attributes:
        tool_name    (str):  The tool that was intercepted.
        tool_args    (dict): The arguments the agent intended to pass.
        tool_call_id (str):  OpenAI tool_call_id — needed to patch the
                             message history after human approval so
                             self.messages stays coherent for the API.
        message      (str):  Human-readable description.

    BEFORE V4 (original): tool_call_id was not stored — this caused
        a 400 error on any subsequent LLM call because the assistant
        message with tool_calls had no matching tool result message.
    AFTER  V4 (fix): tool_call_id is stored here and threaded through
        to execute_approved_hitl_action() which patches the placeholder.
    """

    def __init__(self, tool_name: str, tool_args: dict,
                 tool_call_id: str = ""):
        self.tool_name    = tool_name
        self.tool_args    = tool_args
        self.tool_call_id = tool_call_id          # NEW — needed for message patching
        self.message = (
            f"HITL interrupt: '{tool_name}' requires human approval "
            f"before execution."
        )
        super().__init__(self.message)


def classify_risk(tool_name: str, tool_args: dict) -> str:
    """
    Classify the risk level of a proposed tool call.

    PILLAR 5 — HUMAN-IN-THE-LOOP (risk classification)

    Called inside agent.py's dispatch loop BEFORE executing any
    tool call.  If this returns "HIGH", the caller raises a
    HITLInterrupt instead of executing the tool.

    Args:
        tool_name (str):  The name of the tool the agent wants to call.
        tool_args (dict): The arguments the agent intends to pass.

    Returns:
        str: "HIGH" if human approval is required, "LOW" otherwise.
             Unknown tools default to "HIGH" (fail-safe).

    Example:
        risk = classify_risk("update_patient_record",
                             {"patient_id": "P001", "field": "Diagnosis",
                              "value": "terminal cancer"})
        # → "HIGH"

        risk = classify_risk("list_all_patients", {})
        # → "LOW"
    """
    # Unknown tools default to HIGH — fail-safe over fail-open
    return TOOL_RISK_LEVELS.get(tool_name, "HIGH")


def build_hitl_pending(tool_name: str, tool_args: dict) -> dict:
    """
    Build the pending action dict stored in st.session_state.

    PILLAR 5 — HUMAN-IN-THE-LOOP (state preparation)

    This dict is stored as st.session_state["hitl_pending"] when
    a HIGH RISK tool is intercepted.  The Streamlit UI reads this
    dict to display the approval widget.

    Args:
        tool_name (str):  The intercepted tool name.
        tool_args (dict): The arguments the agent intended to pass.

    Returns:
        dict: Structured pending action for UI consumption.
    """
    return {
        "tool_name":   tool_name,
        "tool_args":   tool_args,
        "description": TOOL_DESCRIPTIONS.get(
            tool_name, f"Execute tool: {tool_name}"
        ),
        "risk_level":  "HIGH",
    }
