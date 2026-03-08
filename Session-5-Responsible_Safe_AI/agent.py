# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : agent.py
# Purpose       : Core Healthcare Agent orchestrator.
#                 Implements a ReAct-style agentic loop using
#                 GPT-4o-mini function calling.  Manages 13 tools
#                 across patient DB, appointments, RAG, and medical
#                 search.  Integrates conversation memory, patient
#                 context tracking, and LLMOps interaction logging.
#
# ══════════════════════════════════════════════════════════════
# V3 vs V4 CHANGES IN THIS FILE
# ══════════════════════════════════════════════════════════════
# This file is MODIFIED from V3.  Search "[V4" to find every
# governance addition and understand exactly what changed.
#
#   [V4 · PILLAR 1 · GUARDRAILS]
#     • input_guardrail()  called at start of chat()
#     • output_guardrail() called on final LLM response
#     • mask_pii()         used before writing to audit log
#
#   [V4 · PILLAR 3 · AUDIT LOG]
#     • log_governance_event() called for every governance event
#       (PII_DETECTED, INPUT_BLOCKED, HITL_TRIGGERED, etc.)
#
#   [V4 · PILLAR 4 · COST CONTROLS]
#     • cost_controller.check_budget() — gate before LLM call
#     • cost_controller.record_usage() — accounting after response
#
#   [V4 · PILLAR 5 · HITL]
#     • classify_risk()  — called before every dispatch_tool()
#     • HITLInterrupt    — raised for HIGH RISK tools
#     • execute_approved_hitl_action() — new method for post-approval
#
#   PILLAR 2 (Evaluation) is wired in the chat page, not here.
#
# ARCHITECTURE — V4 chat() flow:
#
#   chat(user_input)
#       ↓
#   [PILLAR 1] input_guardrail()          → BLOCK? return safe_msg
#       ↓ PASS
#   [PILLAR 4] cost_controller.check()    → HARD_STOP? return msg
#       ↓ OK/WARNING
#   LLM call (GPT-4o-mini)
#       ↓ tool_calls?
#       ├─ YES → [PILLAR 5] classify_risk()
#       │           HIGH → raise HITLInterrupt
#       │           LOW  → dispatch_tool() → loop
#       └─ NO (stop) →
#           [PILLAR 1] output_guardrail()
#           [PILLAR 4] record_usage()
#           [PILLAR 3] log governance events
#           return final_response
# ══════════════════════════════════════════════════════════════

import json
import os
import time
import sys

from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tools.appointment_tool import (
    find_doctors_by_specialty,
    get_available_slots_for_doctor,
    book_appointment,
    cancel_appointment,
    get_patient_appointments,
    get_all_specialties
)
from tools.patient_db_tool import (
    get_patient_by_name,
    get_patient_by_id,
    update_patient_record,
    list_all_patients,
    add_patient_record
)
from tools.rag_tool import retrieve_patient_history, search_across_all_patients
from tools.medical_search_tool import (
    search_medical_information,
    get_disease_overview,
    get_drug_information
)
from memory.memory_module import HealthcareMemory
from prompts.system_prompts import MAIN_SYSTEM_PROMPT

# ── [V4 · PILLAR 1 · GUARDRAILS] ─────────────────────────────
# Import the two-stage safety guardrail and PII masker.
# BEFORE V4: these imports did not exist.
from governance.guardrails import input_guardrail, output_guardrail, mask_pii

# ── [V4 · PILLAR 4 · COST CONTROLS] ──────────────────────────
# Import the session token budget controller.
# BEFORE V4: this import did not exist.
from governance.cost_controller import CostController

# ── [V4 · PILLAR 5 · HITL] ───────────────────────────────────
# Import HITL risk classifier, interrupt exception, and helper.
# BEFORE V4: these imports did not exist.
from governance.hitl_manager import (
    classify_risk,
    HITLInterrupt,
    build_hitl_pending,
)

load_dotenv()


# ── Tool schema definitions ───────────────────────────────────
# V3 — NO CHANGES to TOOLS list in V4.
# OpenAI function-calling schemas for all 13 agent tools.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_doctors_by_specialty",
            "description": "Find available doctors by medical specialty",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {"type": "string", "description": "Medical specialty"}
                },
                "required": ["specialty"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_slots_for_doctor",
            "description": "Get available appointment slots for a specific doctor",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor_id": {"type": "string", "description": "Doctor's ID (e.g. D001)"},
                    "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "num_days":  {"type": "integer","description": "Number of days ahead to check"}
                },
                "required": ["doctor_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a specific appointment slot for a patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id":      {"type": "string", "description": "Slot ID to book"},
                    "patient_id":   {"type": "string", "description": "Patient's ID"},
                    "patient_name": {"type": "string", "description": "Patient's full name"}
                },
                "required": ["slot_id", "patient_id", "patient_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment",
            "parameters": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string", "description": "Slot ID to cancel"}
                },
                "required": ["slot_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_appointments",
            "description": "Get all booked appointments for a patient",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient's ID"}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_by_name",
            "description": "Search for a patient record by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Patient name or partial name"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_by_id",
            "description": "Retrieve a patient record by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient's unique ID"}
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_patient_record",
            "description": "Update a field in a patient's record",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Patient's ID"},
                    "field":      {"type": "string", "description": "Field to update"},
                    "value":      {"type": "string", "description": "New value"}
                },
                "required": ["patient_id", "field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_all_patients",
            "description": "List all patients in the system",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_patient_history",
            "description": "Retrieve patient medical history using RAG (FAISS + GPT-4o-mini)",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string", "description": "Patient's full name"},
                    "query":        {"type": "string", "description": "Specific question (optional)"}
                },
                "required": ["patient_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_medical_information",
            "description": "Search MedlinePlus/WHO for trusted medical information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Medical topic or question"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_disease_overview",
            "description": "Get a comprehensive overview of a disease or condition",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease_name": {"type": "string", "description": "Disease or condition name"}
                },
                "required": ["disease_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_drug_information",
            "description": "Get information about a drug including uses, dosage, side effects",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string", "description": "Drug or medication name"}
                },
                "required": ["drug_name"]
            }
        }
    }
]


# ── Tool dispatcher map ───────────────────────────────────────
# V3 — NO CHANGES to TOOL_MAP in V4.

TOOL_MAP = {
    "find_doctors_by_specialty":      find_doctors_by_specialty,
    "get_available_slots_for_doctor": get_available_slots_for_doctor,
    "book_appointment":               book_appointment,
    "cancel_appointment":             cancel_appointment,
    "get_patient_appointments":       get_patient_appointments,
    "get_patient_by_name":            get_patient_by_name,
    "get_patient_by_id":              get_patient_by_id,
    "update_patient_record":          update_patient_record,
    "list_all_patients":              list_all_patients,
    "retrieve_patient_history":       retrieve_patient_history,
    "search_medical_information":     search_medical_information,
    "get_disease_overview":           get_disease_overview,
    "get_drug_information":           get_drug_information,
}


def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    """
    Dispatch a tool call by name with the provided arguments.

    V3 — This function body is UNCHANGED from V3.
    V4 — HITL risk classification now happens in chat() BEFORE
         this function, so arriving here means the tool is either
         LOW RISK or has been approved by a human.

    Args:
        tool_name (str):  Name of the tool to invoke.
        tool_args (dict): Arguments for the tool function.

    Returns:
        str: JSON result from the tool, or error JSON on failure.
    """
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return fn(**tool_args)
    except Exception as e:
        return json.dumps({"error": f"Tool '{tool_name}' failed: {str(e)}"})


# ── Healthcare Agent ──────────────────────────────────────────

class HealthcareAgent:
    """
    V4 Agentic Healthcare Assistant orchestrator.

    Wraps the V3 ReAct agent loop with all 5 responsible AI
    governance pillars.  All V3 capabilities are preserved
    and extended — nothing was removed.

    V3 capabilities (unchanged):
        GPT-4o-mini function calling, 13 tools, sliding-window
        conversation memory, active patient context, LLMOps logging.

    V4 governance additions:
        [PILLAR 1] input_guardrail() and output_guardrail()
        [PILLAR 3] log_governance_event() for audit trail
        [PILLAR 4] CostController — token budget enforcement
        [PILLAR 5] classify_risk() + HITLInterrupt pattern

    Attributes:
        client           (OpenAI):          OpenAI API client.
        model            (str):             GPT model name.
        memory           (HealthcareMemory):Conversation + patient ctx.
        messages         (list):            Message history for API.
        session_id       (str):             Session identifier.
        enable_logging   (bool):            LLMOps logging flag.
        last_tools_used  (list):            Tools from last chat() call.
        cost_controller  (CostController):  [V4] Token budget tracker.
        guardrail_events (list):            [V4] This session's events.
    """

    def __init__(self, session_id: str = "default", enable_logging: bool = True):
        """
        Initialise the Healthcare Agent with all V4 governance layers.

        Args:
            session_id     (str):  Session identifier used in all logs.
            enable_logging (bool): Whether to write interaction logs.
        """
        self.client          = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model           = "gpt-4o-mini"
        self.memory          = HealthcareMemory(window_size=10)
        self.messages        = []
        self.session_id      = session_id
        self.enable_logging  = enable_logging
        self.last_tools_used = []

        # [V4 · PILLAR 4 · COST CONTROLS] ─────────────────────
        # One CostController per agent instance.
        # Tracks cumulative tokens across all chat() calls.
        # Resets when reset_session() is called.
        self.cost_controller = CostController(session_id=session_id)

        # [V4 · PILLAR 1 · GUARDRAILS] ────────────────────────
        # List of guardrail events from this session.
        # Read by the Governance Dashboard for pillar 1 metrics.
        self.guardrail_events = []

        # Bind V3 logger functions at init time
        if self.enable_logging:
            try:
                from evaluation.logger import log_tool_call, log_interaction
                self._log_tool_call   = log_tool_call
                self._log_interaction = log_interaction
            except ImportError:
                self.enable_logging = False

    def _build_system_message(self) -> str:
        """Build system prompt with active patient context. V3 unchanged."""
        return MAIN_SYSTEM_PROMPT.format(
            patient_context=self.memory.get_patient_context_string()
        )

    def _log_tool(self, tool_name, tool_args, tool_result, elapsed_ms):
        """Log a tool call. Skips book_appointment (logged elsewhere). V3 unchanged."""
        if not self.enable_logging:
            return
        if tool_name == "book_appointment":
            return
        try:
            self._log_tool_call(
                tool_name=tool_name,
                tool_args=tool_args,
                tool_result=tool_result,
                success=True,
                execution_time_ms=elapsed_ms,
                session_id=self.session_id
            )
        except Exception:
            pass

    def _log_gov(self, event_type, **kwargs):
        """
        Convenience wrapper for log_governance_event.

        [V4 · PILLAR 3 · AUDIT LOG] — NEW helper in V4.

        Silently swallows exceptions so governance logging
        never breaks the main chat flow.
        """
        if not self.enable_logging:
            return
        try:
            from evaluation.logger import log_governance_event
            log_governance_event(
                event_type = event_type,
                session_id = self.session_id,
                **kwargs
            )
        except Exception:
            pass

    def chat(self, user_input: str, verbose: bool = True) -> str:
        """
        Process a user message through the V4 governance-augmented
        agentic loop and return the final text response.

        V4 FLOW (search '[V4' to locate each addition):
          1. [V4 · PILLAR 1] input_guardrail() — block PII/harmful
          2. [V4 · PILLAR 4] cost_controller.check_budget()
          3. System message update  (V3 unchanged)
          4. LLM call loop:
             a. GPT-4o-mini call  (V3 unchanged)
             b. Tool calls:
                [V4 · PILLAR 5] classify_risk() → HIGH → HITLInterrupt
                LOW → dispatch_tool()  (V3 unchanged path)
             c. finish=stop:
                [V4 · PILLAR 1] output_guardrail()
                [V4 · PILLAR 4] record_usage()
                return response
          5. Memory + logging  (V3 unchanged)

        Args:
            user_input (str):  Raw user message string.
            verbose    (bool): Print tool traces to stdout.

        Returns:
            str: Final agent response (possibly with safety footer).

        Raises:
            HITLInterrupt: Propagated to the Streamlit chat page
                           when a HIGH RISK tool is intercepted.
                           The page stores the pending action in
                           st.session_state["hitl_pending"] before
                           re-raising, then shows the approval widget.
        """
        interaction_start = time.time()
        self.last_tools_used = []

        # ─────────────────────────────────────────────────────
        # [V4 · PILLAR 1 · GUARDRAILS] — Stage 1: Input check
        # ─────────────────────────────────────────────────────
        # BEFORE V4: user_input flowed directly to the LLM.
        # AFTER  V4: input_guardrail() intercepts PII and harmful
        #            queries before a single token is spent.
        guardrail_result = input_guardrail(user_input)
        if guardrail_result["action"] == "BLOCK":
            event_type = (
                "PII_DETECTED"
                if guardrail_result["pii_detected"]
                else "INPUT_BLOCKED"
            )
            self._log_gov(
                event_type    = event_type,
                query_preview = mask_pii(user_input[:100]),
                risk_level    = "HIGH",
                pii_detected  = guardrail_result["pii_detected"] or "",
                details       = guardrail_result["reason"],
            )
            self.guardrail_events.append(guardrail_result)
            return guardrail_result["safe_message"]

        # ─────────────────────────────────────────────────────
        # [V4 · PILLAR 4 · COST CONTROLS] — Budget gate
        # ─────────────────────────────────────────────────────
        # BEFORE V4: no token budget — unlimited LLM calls.
        # AFTER  V4: hard stop if session budget is exhausted.
        budget = self.cost_controller.check_budget()
        if not budget["can_proceed"]:
            self._log_gov(
                event_type    = "COST_HARD_STOP",
                query_preview = user_input[:100],
                risk_level    = "HIGH",
                details       = budget["message"],
            )
            return budget["message"]

        # Warn in verbose mode (doesn't block, just informs)
        if verbose and budget["state"] == "WARNING":
            print(f"\n  ⚠️  Cost warning: {budget['message']}")
            self._log_gov(
                event_type    = "COST_WARNING",
                query_preview = user_input[:100],
                risk_level    = "MEDIUM",
                details       = budget["message"],
            )

        # ── System message update (V3 unchanged) ─────────────
        if not self.messages:
            self.messages.append({
                "role":    "system",
                "content": self._build_system_message()
            })
        else:
            self.messages[0]["content"] = self._build_system_message()

        self.messages.append({"role": "user", "content": user_input})

        if verbose:
            print(f"\n{'─'*60}\n🤔 Agent Processing...")

        # ── ReAct agentic loop (V3 core — V4 additions inside) ─
        max_iterations = 10
        for iteration in range(max_iterations):

            # LLM call — V3 unchanged
            response      = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=2000
            )
            message       = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            msg_dict = {
                "role":       "assistant",
                "content":    message.content,
                "tool_calls": [
                    {
                        "id":   tc.id,
                        "type": "function",
                        "function": {
                            "name":      tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (message.tool_calls or [])
                ] if message.tool_calls else None
            }
            self.messages.append(msg_dict)

            # ── Final response path ───────────────────────────
            if finish_reason == "stop" or not message.tool_calls:
                raw_response = message.content or "I couldn't generate a response."

                # ─────────────────────────────────────────────
                # [V4 · PILLAR 1 · GUARDRAILS] — Stage 2: Output
                # ─────────────────────────────────────────────
                # BEFORE V4: LLM response returned as-is.
                # AFTER  V4: output_guardrail() appends safety footer
                #            when dosage numbers / risky content found.
                final_response = output_guardrail(raw_response)
                if final_response != raw_response:
                    self._log_gov(
                        event_type    = "OUTPUT_FLAGGED",
                        query_preview = user_input[:100],
                        risk_level    = "MEDIUM",
                        details       = "Safety disclaimer footer appended to output",
                    )

                # ─────────────────────────────────────────────
                # [V4 · PILLAR 4 · COST CONTROLS] — Record usage
                # ─────────────────────────────────────────────
                # BEFORE V4: no token accounting.
                # AFTER  V4: record actual tokens from OpenAI usage
                #            object (or estimate if unavailable).
                actual_tokens = None
                try:
                    if response.usage:
                        actual_tokens = response.usage.total_tokens
                except Exception:
                    pass
                self.cost_controller.record_usage(
                    user_input     = user_input,
                    agent_response = final_response,
                    actual_tokens  = actual_tokens,
                )

                # Memory + V3 interaction log (unchanged)
                self.memory.add_interaction(user_input, final_response)
                if self.enable_logging:
                    elapsed_ms = (time.time() - interaction_start) * 1000
                    try:
                        self._log_interaction(
                            user_input=user_input,
                            agent_response=final_response,
                            tools_used=self.last_tools_used,
                            response_time_ms=elapsed_ms,
                            session_id=self.session_id
                        )
                    except Exception:
                        pass

                return final_response

            # ── Tool execution path ───────────────────────────
            for tool_call in message.tool_calls:
                tool_name  = tool_call.function.name
                tool_start = time.time()

                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                # ─────────────────────────────────────────────
                # [V4 · PILLAR 5 · HITL] — Risk gate
                # ─────────────────────────────────────────────
                # BEFORE V4: dispatch_tool() called immediately.
                # AFTER  V4: classify_risk() runs first.
                #   HIGH → log event, raise HITLInterrupt
                #           (caller stores pending action in
                #            st.session_state and shows widget)
                #   LOW  → dispatch_tool() as before (V3 path)
                risk = classify_risk(tool_name, tool_args)
                if risk == "HIGH":
                    self._log_gov(
                        event_type    = "HITL_TRIGGERED",
                        tool_name     = tool_name,
                        query_preview = user_input[:100],
                        risk_level    = "HIGH",
                        details       = (
                            f"HITL interrupt for {tool_name}: "
                            f"{json.dumps(tool_args)[:200]}"
                        ),
                    )
                    # ─────────────────────────────────────────
                    # BEFORE V4 (bug): raised HITLInterrupt with
                    #   no tool result in self.messages, leaving an
                    #   orphaned assistant tool_calls entry → 400 on
                    #   the next API call.
                    # AFTER  V4 (fix): append a placeholder tool
                    #   result immediately so self.messages is always
                    #   coherent.  execute_approved_hitl_action() will
                    #   patch this placeholder with the real result.
                    self.messages.append({
                        "role":         "tool",
                        "tool_call_id": tool_call.id,
                        "content":      json.dumps({
                            "status": "pending_human_approval",
                            "tool":   tool_name,
                        }),
                    })
                    raise HITLInterrupt(tool_name, tool_args,
                                        tool_call_id=tool_call.id)

                # LOW RISK — original V3 dispatch path
                tool_result  = dispatch_tool(tool_name, tool_args)
                tool_elapsed = (time.time() - tool_start) * 1000

                if tool_name not in self.last_tools_used:
                    self.last_tools_used.append(tool_name)

                if verbose:
                    preview = (tool_result[:200] + "..."
                               if len(tool_result) > 200 else tool_result)
                    print(f"\n  🔧 Tool: {tool_name}")
                    print(f"     Args: {json.dumps(tool_args)}")
                    print(f"     Result: {preview}")

                self._log_tool(tool_name, tool_args, tool_result, tool_elapsed)

                self.messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      tool_result
                })

                # Update patient context from lookup (V3 unchanged)
                if tool_name in ["get_patient_by_name", "get_patient_by_id"]:
                    try:
                        result_data = json.loads(tool_result)
                        if result_data.get("status") == "success":
                            patient = result_data.get("patient") or (
                                result_data.get("patients", [{}])[0]
                            )
                            if patient:
                                self.memory.set_patient_context(patient)
                    except Exception:
                        pass

        return "I've completed processing your request. Let me know if you need anything else."

    def execute_approved_hitl_action(
        self,
        tool_name:    str,
        tool_args:    dict,
        decision:     str = "APPROVED",
        tool_call_id: str = "",
    ) -> str:
        """
        Execute a tool call that has been approved via the HITL widget.

        [V4 · PILLAR 5 · HITL] — NEW method in V4.
        [V4 · HITL BUG FIX]    — tool_call_id + message patching added.

        BEFORE V4 (bug): dispatched tool, returned raw JSON to UI.
            self.messages had an orphaned placeholder tool result that
            was never replaced — next chat call produced a 400 error.

        AFTER  V4 (fix):
            1. Replace the placeholder in self.messages with the real
               tool result (matched by tool_call_id).
            2. Call LLM once more (tool_choice="none") to get a natural
               language response confirming the action.
            3. Apply output_guardrail() before returning to UI.

        Args:
            tool_name    (str):  The approved tool name.
            tool_args    (dict): Approved (or edited) tool arguments.
            decision     (str):  "APPROVED" | "EDITED" for audit log.
            tool_call_id (str):  OpenAI tool_call_id from HITLInterrupt
                                 — used to patch the placeholder message.

        Returns:
            str: Natural language LLM response, or error message.
        """
        try:
            # Step 1 — Execute the approved tool
            tool_result = dispatch_tool(tool_name, tool_args)

            # Step 2 — Audit log
            event_type = "HITL_EDITED" if decision == "EDITED" else "HITL_APPROVED"
            self._log_gov(
                event_type = event_type,
                tool_name  = tool_name,
                risk_level = "HIGH",
                decision   = decision,
                details    = (
                    f"Executed after human {decision}. "
                    f"Args: {json.dumps(tool_args)[:200]}"
                ),
            )
            if tool_name not in self.last_tools_used:
                self.last_tools_used.append(tool_name)

            # Step 3 — Patch the placeholder in self.messages
            # HITLInterrupt left a {"status":"pending_human_approval"}
            # placeholder.  Replace it with the real result so the
            # conversation history is coherent for the next API call.
            patched = False
            if tool_call_id:
                for i, msg in enumerate(self.messages):
                    if (msg.get("role") == "tool"
                            and msg.get("tool_call_id") == tool_call_id
                            and "pending_human_approval" in msg.get("content", "")):
                        self.messages[i]["content"] = tool_result
                        patched = True
                        break
            if not patched:
                self.messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call_id or "hitl_approved",
                    "content":      tool_result,
                })

            # Step 4 — Ask LLM to produce a natural language response
            follow_up = self.client.chat.completions.create(
                model       = self.model,
                messages    = self.messages,
                tools       = TOOLS,
                tool_choice = "none",
                temperature = 0.2,
                max_tokens  = 500,
            )
            raw_response = (
                follow_up.choices[0].message.content
                or "Action completed successfully."
            )
            self.messages.append({
                "role":       "assistant",
                "content":    raw_response,
                "tool_calls": None,
            })

            # Step 5 — Output guardrail
            return output_guardrail(raw_response)

        except Exception as e:
            return json.dumps({"error": str(e)})

    def reset_session(self):
        """
        Reset the agent to a clean state for a new conversation.

        V3 — cleared messages, tool traces, and memory.
        V4 — ALSO resets cost_controller and guardrail_events.
        """
        self.messages         = []
        self.last_tools_used  = []
        self.guardrail_events = []          # [V4 · PILLAR 1]
        self.memory.clear_conversation()
        self.memory.clear_patient_context()
        self.cost_controller.reset()        # [V4 · PILLAR 4]
