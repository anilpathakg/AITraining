# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# File    : governance/guardrails.py
# Author  : Anil Pathak
# Purpose : Implements Pillar 1 — Safety Guardrails.
#
# ══════════════════════════════════════════════════════════════
# GOVERNANCE PILLAR 1 — SAFETY GUARDRAILS
# ══════════════════════════════════════════════════════════════
#
# WHY THIS EXISTS:
#   Agentic AI systems operate autonomously and can receive
#   harmful, sensitive, or dangerous inputs before the LLM
#   ever processes them.  Without a guardrail layer, the agent
#   could:
#     • Leak patient PII (SSN, Aadhaar) into logs or responses
#     • Answer questions about lethal drug dosages
#     • Return medically unsafe outputs without disclaimers
#
#   This module provides a two-stage defence:
#     Stage 1 — INPUT GUARDRAIL  : runs BEFORE the agent
#     Stage 2 — OUTPUT GUARDRAIL : runs AFTER the agent
#
# ARCHITECTURE (where this sits):
#
#   User Input
#       ↓
#   [input_guardrail()]   ← THIS FILE (Stage 1)
#       ↓  PASS
#   agent.chat()          ← existing ReAct loop (unchanged)
#       ↓
#   [output_guardrail()]  ← THIS FILE (Stage 2)
#       ↓
#   Final response shown to user
#
# WHAT IT DETECTS:
#   INPUT:
#     - PII patterns  : SSN (xxx-xx-xxxx), Aadhaar (12-digit),
#                       phone numbers (10-digit), email addresses
#     - Harmful queries: lethal dosages, self-harm, poison info
#   OUTPUT:
#     - Responses missing the professional-consultation disclaimer
#       when drug/dosage content is detected
#     - Responses containing absolute dosage advice without caveats
#
# DESIGN DECISIONS:
#   • Regex-first (fast, no LLM call) for PII — patterns are
#     deterministic and well-defined.
#   • Keyword list for harmful queries — covers the most common
#     dangerous medical question patterns without false positives.
#   • Output check is lightweight — checks for known risk patterns
#     and injects a safety footer rather than blocking.
#   • Returns structured dicts so the caller (agent/chat page) can
#     act on action, reason, and pii_detected independently.
#
# TEACHING NOTE FOR STUDENTS:
#   Notice the separation of concerns: input_guardrail() BLOCKS
#   before any LLM call (zero token cost, instant).
#   output_guardrail() MODIFIES after the LLM responds (adds a
#   safety footer). This asymmetry is intentional — blocking on
#   input is cheaper and safer; modifying on output handles the
#   cases that slip through.
# ══════════════════════════════════════════════════════════════

import re
import json
import logging
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


# ── PII detection patterns ────────────────────────────────────
# Each pattern is a compiled regex for performance.
# These cover the most common PII types seen in healthcare
# contexts (Indian + US identifiers).

_PII_PATTERNS = {
    "SSN": re.compile(
        r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"
    ),
    "Aadhaar": re.compile(
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
    ),
    "Phone_IN": re.compile(
        r"\b[6-9]\d{9}\b"               # Indian mobile (starts 6-9)
    ),
    "Phone_US": re.compile(
        r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    ),
    "Email": re.compile(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    ),
    "Credit_Card": re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
    ),
}

# ── Harmful query pre-filter triggers (Layer 1B) ─────────────
# BEFORE V4: This list was the SOLE decision mechanism for
#            harmful query detection (keyword → BLOCK).
# AFTER  V4: This list is now a CHEAP PRE-FILTER only.
#            If ANY trigger is found → escalate to LLM judge (Layer 2).
#            If NO trigger is found  → pass directly (zero LLM cost).
#
# The LLM judge (_call_llm_classifier) makes the final decision.
# This means the list can be BROADER than before — false positives
# here only cost one extra LLM call, they no longer cause false blocks.

_HARMFUL_TRIGGERS = [
    "lethal dose",
    "lethal dosage",
    "how to kill",
    "suicide method",
    "how to commit suicide",
    "how to overdose",
    "fatal dose",
    "fatal amount",
    "how much to die",
    "poison someone",
    "how to poison",
    "drug to kill",
    "medication to kill",
    "overdose on purpose",
    "self harm method",
    "how to self harm",
    "lethal",        # broader triggers safe to add now — LLM decides
    "fatal",
    "toxic dose",
    "overdose",
]

# ── Output risk patterns ──────────────────────────────────────
# Patterns in LLM output that warrant a safety footer being added.
# We do NOT block output — we append a disclaimer instead.

_OUTPUT_RISK_PATTERNS = [
    re.compile(r"\b\d+\s*mg\b", re.IGNORECASE),    # Dosage numbers
    re.compile(r"\b\d+\s*mcg\b", re.IGNORECASE),
    re.compile(r"\bmax(imum)?\s+dose\b", re.IGNORECASE),
    re.compile(r"\blethal\b", re.IGNORECASE),
    re.compile(r"\boverdose\b", re.IGNORECASE),
]

_SAFETY_FOOTER = (
    "\n\n---\n"
    "⚠️ **Safety Notice:** This information is for general reference "
    "only and does not replace the advice of a qualified healthcare "
    "professional. Always consult your doctor or pharmacist before "
    "making any medical decisions."
)


# ══════════════════════════════════════════════════════════════
# PRIVATE — LLM-as-Judge classifier (Layer 2)
# ══════════════════════════════════════════════════════════════

def _call_llm_classifier(text: str) -> dict:
    """
    Layer 2 — LLM-as-Judge harmful query classifier.

    Called ONLY when Layer 1B (keyword pre-filter) detects a
    suspicious trigger in the input.  Makes the final HARMFUL /
    SAFE classification using GPT-4o-mini.

    PILLAR 1 — SAFETY GUARDRAILS (LLM judge, Layer 2)

    FAIL-CLOSED: Any exception (network error, timeout, bad JSON,
    unexpected response) returns BLOCK.  In a healthcare system,
    blocking a legitimate query is safer than passing a harmful one.

    Args:
        text (str): The raw user input to classify.

    Returns:
        dict with keys:
            classification (str): "HARMFUL" | "SAFE"
            reason         (str): One-sentence explanation
            confidence   (float): 0.0–1.0
            source         (str): "llm_judge" | "fail_closed"
    """
    # Import here to avoid circular import at module load time
    from prompts.system_prompts import HARM_CLASSIFIER_PROMPT

    try:
        client = OpenAI()
        prompt = HARM_CLASSIFIER_PROMPT.format(query=text)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,          # deterministic classification
            max_tokens=120,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them despite instructions
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("```").strip()

        result = json.loads(raw)

        # Validate expected keys are present
        classification = result.get("classification", "").upper()
        if classification not in ("HARMFUL", "SAFE"):
            raise ValueError(f"Unexpected classification: {classification!r}")

        return {
            "classification": classification,
            "reason":         result.get("reason", "LLM judge decision"),
            "confidence":     float(result.get("confidence", 0.9)),
            "source":         "llm_judge",
        }

    except Exception as exc:
        # FAIL-CLOSED: any failure → block the query
        logger.warning("LLM safety classifier failed — fail-closed. Error: %s", exc)
        return {
            "classification": "HARMFUL",
            "reason":         "Safety classifier unavailable — blocked by default (fail-closed)",
            "confidence":     1.0,
            "source":         "fail_closed",
        }


# ══════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════

def input_guardrail(text: str) -> dict:
    """
    Stage 1 — Input Guardrail.

    Scans the user raw input BEFORE it is sent to the LLM agent.
    Uses a TWO-LAYER approach to detect harmful queries:

    PILLAR 1 — SAFETY GUARDRAILS (input side)

    BEFORE V4: Step 2 was keyword list → immediate BLOCK.
    AFTER  V4: Step 2 keyword match → escalate to LLM judge.
               The LLM judge makes the final HARMFUL/SAFE call,
               understanding INTENT not just surface keywords.

    Architecture:
        Layer 1A — PII regex          (always, instant, zero tokens)
        Layer 1B — Keyword pre-filter (always, instant, zero tokens)
            ↓ keyword found
        Layer 2  — LLM-as-judge       (~500ms, ~100 tokens)
            HARMFUL  → BLOCK
            SAFE     → PASS
            ERROR    → BLOCK  (fail-closed — healthcare default)

    Args:
        text (str): The raw user input string.

    Returns:
        dict with keys:
            action          (str):        "PASS" | "BLOCK"
            reason          (str):        Human-readable reason
            pii_detected    (str | None): PII type if found, else None
            safe_message    (str | None): Message to show user if BLOCK
            classifier_used (str | None): "llm_judge"|"fail_closed"|None
    """

    # ── Layer 1A: PII check ───────────────────────────────────
    for pii_type, pattern in _PII_PATTERNS.items():
        if pattern.search(text):
            return {
                "action":          "BLOCK",
                "reason":          f"PII detected in input: {pii_type}",
                "pii_detected":    pii_type,
                "classifier_used": None,
                "safe_message": (
                    f"🔐 **Input Blocked — {pii_type} Detected**\n\n"
                    f"Your message appears to contain a **{pii_type}** "
                    f"(Personal Identifiable Information). For patient "
                    f"safety and data privacy, this query has been blocked "
                    f"and the event logged to the audit trail.\n\n"
                    f"Please remove the sensitive information and rephrase "
                    f"your question."
                ),
            }

    # ── Layer 1B: Keyword pre-filter ──────────────────────────
    # BEFORE V4: keyword match → BLOCK immediately.
    # AFTER  V4: keyword match → trigger LLM judge (Layer 2).
    #            Clean queries (no trigger) pass with zero LLM cost.
    lower = text.lower()
    triggered_keyword = None
    for trigger in _HARMFUL_TRIGGERS:
        if trigger in lower:
            triggered_keyword = trigger
            break

    if triggered_keyword is None:
        return {
            "action":          "PASS",
            "reason":          "OK",
            "pii_detected":    None,
            "classifier_used": None,
            "safe_message":    None,
        }

    # ── Layer 2: LLM-as-judge classifier ─────────────────────
    # Keyword found — ask LLM to decide: is the INTENT harmful?
    # This correctly distinguishes:
    #   "What is the lethal dose of X?"    → HARMFUL (blocked)
    #   "What are toxic effects of X?"     → SAFE    (passes)
    classifier_result = _call_llm_classifier(text)

    if classifier_result["classification"] == "HARMFUL":
        source = classifier_result["source"]
        reason_detail = classifier_result["reason"]
        return {
            "action":          "BLOCK",
            "reason":          f"Harmful query — {reason_detail} [{source}]",
            "pii_detected":    None,
            "classifier_used": source,
            "safe_message": (
                "🚫 **Query Blocked — Safety Guardrail**\n\n"
                "This query has been identified as potentially harmful "
                "(requesting dangerous medical information). Such "
                "requests are blocked by the safety guardrail to "
                "protect patient and user wellbeing.\n\n"
                "If you need drug safety or dosage information for "
                "legitimate clinical purposes, please consult official "
                "clinical databases such as MedlinePlus or contact a "
                "licensed pharmacist."
            ),
        }

    # LLM judge returned SAFE — pass to agent
    return {
        "action":          "PASS",
        "reason":          f"LLM judge: SAFE — {classifier_result['reason']}",
        "pii_detected":    None,
        "classifier_used": classifier_result["source"],
        "safe_message":    None,
    }


def output_guardrail(text: str) -> str:
    """
    Stage 2 — Output Guardrail.

    Scans the agent's response AFTER it is generated by the LLM.
    If the response contains dosage numbers or other risky patterns,
    a safety disclaimer footer is appended.

    PILLAR 1 — SAFETY GUARDRAILS (output side)

    Design choice: We append (not block) on output because:
      • The LLM may have legitimately answered a clinical question
      • Blocking the output would break the user experience
      • A safety footer is the industry-standard approach

    Args:
        text (str): The agent's raw response string.

    Returns:
        str: The response unchanged (if safe), or with a safety
             footer appended (if risky patterns detected).

    Example:
        safe_output = output_guardrail("Take 500mg of Metformin.")
        # → "Take 500mg of Metformin.\n\n---\n⚠️ Safety Notice: ..."
    """
    for pattern in _OUTPUT_RISK_PATTERNS:
        if pattern.search(text):
            # Only append footer if not already present
            if "Safety Notice" not in text:
                return text + _SAFETY_FOOTER
            break
    return text


def mask_pii(text: str) -> str:
    """
    Replace PII patterns in a string with masked placeholders.
    Used when storing user inputs in the audit log to avoid
    persisting real PII to disk.

    PILLAR 1 — SAFETY GUARDRAILS (audit log sanitisation)

    Args:
        text (str): Raw text that may contain PII.

    Returns:
        str: Text with PII replaced by [REDACTED-<type>] tokens.

    Example:
        mask_pii("My SSN is 123-45-6789 and email is x@y.com")
        # → "My SSN is [REDACTED-SSN] and email is [REDACTED-Email]"
    """
    masked = text
    for pii_type, pattern in _PII_PATTERNS.items():
        masked = pattern.sub(f"[REDACTED-{pii_type}]", masked)
    return masked
