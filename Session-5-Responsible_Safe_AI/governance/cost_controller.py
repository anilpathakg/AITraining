# =============================================================
# Anil Pathak's Agentic Healthcare Assistant  —  V4
# Session 5: Engineering, Deploying and Governing
#            Responsible & Safe Agentic AI Systems
# =============================================================
# File    : governance/cost_controller.py
# Author  : Anil Pathak
# Purpose : Implements Pillar 4 — Cost Controls.
#
# ══════════════════════════════════════════════════════════════
# GOVERNANCE PILLAR 4 — COST CONTROLS
# ══════════════════════════════════════════════════════════════
#
# WHY THIS EXISTS:
#   Agentic AI systems can run multi-step ReAct loops, call
#   multiple tools, and generate long responses — all of which
#   consume tokens and incur API costs.  In a production system,
#   uncontrolled token usage leads to:
#     • Unexpected billing spikes
#     • Runaway loops that never terminate
#     • Denial-of-service from a single session
#
#   This module tracks token usage per session and enforces
#   a hard budget ceiling with a soft warning threshold.
#
# ARCHITECTURE (where this sits):
#
#   User Input
#       ↓
#   input_guardrail()
#       ↓
#   [cost_controller.check_budget()]  ← THIS FILE
#       ↓  OK / WARNING
#   agent.chat()
#       ↓
#   [cost_controller.record_usage()]  ← THIS FILE (post-call)
#       ↓
#   Final response
#
# TOKEN BUDGET STATES:
#
#   OK        → budget < WARNING_THRESHOLD
#                 Normal operation, green indicator in UI
#   WARNING   → WARNING_THRESHOLD ≤ budget < HARD_STOP_THRESHOLD
#                 User sees orange indicator and warning message
#   HARD_STOP → budget ≥ HARD_STOP_THRESHOLD
#                 Agent call is BLOCKED, user sees red indicator
#
# TOKEN COUNTING APPROACH:
#   We use a simple approximation: 1 token ≈ 4 characters.
#   This avoids adding the `tiktoken` dependency while giving
#   a reasonable estimate for GPT-4o-mini.
#   In production, use tiktoken.encoding_for_model() for accuracy.
#
# COST CALCULATION:
#   GPT-4o-mini pricing (as of 2025):
#     Input tokens  : $0.150 per 1M tokens
#     Output tokens : $0.600 per 1M tokens
#   We use a blended rate of $0.30 per 1M tokens for simplicity.
#
# TEACHING NOTE FOR STUDENTS:
#   The three-state budget (OK → WARNING → HARD_STOP) is a
#   real pattern used in production LLM platforms.  It mirrors
#   rate-limiting patterns in traditional APIs but adapted for
#   the non-deterministic token usage of LLM agents.
#   The WARNING state is crucial — it gives operators a chance
#   to intervene before the hard stop disrupts users.
# ══════════════════════════════════════════════════════════════

import time
from typing import Optional


# ── Budget thresholds ─────────────────────────────────────────
# These are session-level limits (reset on new session).
# Adjust for your deployment — these are tuned for demo purposes.

HARD_STOP_THRESHOLD  = 10_000   # tokens — block further calls
WARNING_THRESHOLD    =  7_000   # tokens — warn user, allow calls

# Blended cost per token (input + output average, GPT-4o-mini)
COST_PER_TOKEN = 0.00000030     # $0.30 per 1M tokens


# ── Budget state constants ────────────────────────────────────
STATE_OK        = "OK"
STATE_WARNING   = "WARNING"
STATE_HARD_STOP = "HARD_STOP"


def _estimate_tokens(text: str) -> int:
    """
    Estimate the token count for a given string.

    Uses the 4-chars-per-token heuristic — accurate to ±15% for
    English medical text with GPT-4o-mini tokenisation.

    For production use, replace with:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4o-mini")
        return len(enc.encode(text))

    Args:
        text (str): Any string (user input or agent response).

    Returns:
        int: Estimated token count (minimum 1).
    """
    return max(1, len(text) // 4)


class CostController:
    """
    Session-scoped token budget tracker and enforcement gate.

    PILLAR 4 — COST CONTROLS

    Tracks cumulative token usage across all interactions in a
    session and enforces configurable WARNING and HARD_STOP
    thresholds.

    Attributes:
        session_id           (str):   Unique session identifier.
        total_tokens         (int):   Cumulative tokens this session.
        total_cost_usd       (float): Estimated USD cost this session.
        query_count          (int):   Number of queries processed.
        hard_stop_threshold  (int):   Token count for HARD_STOP state.
        warning_threshold    (int):   Token count for WARNING state.
        _query_log           (list):  Per-query token breakdown.

    Example:
        controller = CostController(session_id="sess_001")
        status = controller.check_budget()
        # → {"state": "OK", "can_proceed": True, ...}

        controller.record_usage("What is hypertension?", "Hyper...", 320)
        summary = controller.get_summary()
    """

    def __init__(
        self,
        session_id: str = "default",
        hard_stop_threshold: int  = HARD_STOP_THRESHOLD,
        warning_threshold: int    = WARNING_THRESHOLD,
    ):
        """
        Initialise a new cost controller for a session.

        Args:
            session_id           (str): Session identifier for logging.
            hard_stop_threshold  (int): Token limit for HARD_STOP.
            warning_threshold    (int): Token limit for WARNING.
        """
        self.session_id          = session_id
        self.hard_stop_threshold = hard_stop_threshold
        self.warning_threshold   = warning_threshold

        # Cumulative session counters
        self.total_tokens   = 0
        self.total_cost_usd = 0.0
        self.query_count    = 0
        self._query_log     = []      # List of per-query dicts
        self._session_start = time.time()

    # ── Core gate ─────────────────────────────────────────────

    def check_budget(self) -> dict:
        """
        Check the current budget state BEFORE an agent call.

        PILLAR 4 — COST CONTROLS (pre-call gate)

        Called by the chat page before invoking agent.chat().
        If state is HARD_STOP, the caller should NOT proceed.

        Returns:
            dict with keys:
                state        (str):   "OK" | "WARNING" | "HARD_STOP"
                can_proceed  (bool):  True if agent call is allowed.
                tokens_used  (int):   Total tokens consumed so far.
                tokens_left  (int):   Tokens remaining before hard stop.
                pct_used     (float): Percentage of hard stop used.
                cost_usd     (float): Estimated cost so far.
                message      (str):   Human-readable status message.

        Example:
            status = controller.check_budget()
            if not status["can_proceed"]:
                st.error(status["message"])
                return
        """
        pct = (self.total_tokens / self.hard_stop_threshold) * 100

        if self.total_tokens >= self.hard_stop_threshold:
            return {
                "state":       STATE_HARD_STOP,
                "can_proceed": False,
                "tokens_used": self.total_tokens,
                "tokens_left": 0,
                "pct_used":    min(pct, 100.0),
                "cost_usd":    self.total_cost_usd,
                "message": (
                    f"🛑 **Session token budget exhausted** "
                    f"({self.total_tokens:,} / {self.hard_stop_threshold:,} tokens). "
                    f"Please start a new session to continue."
                ),
            }

        if self.total_tokens >= self.warning_threshold:
            left = self.hard_stop_threshold - self.total_tokens
            return {
                "state":       STATE_WARNING,
                "can_proceed": True,
                "tokens_used": self.total_tokens,
                "tokens_left": left,
                "pct_used":    pct,
                "cost_usd":    self.total_cost_usd,
                "message": (
                    f"⚠️ **Token budget warning** — "
                    f"{self.total_tokens:,} / {self.hard_stop_threshold:,} tokens used "
                    f"(${self.total_cost_usd:.4f}). "
                    f"{left:,} tokens remaining."
                ),
            }

        return {
            "state":       STATE_OK,
            "can_proceed": True,
            "tokens_used": self.total_tokens,
            "tokens_left": self.hard_stop_threshold - self.total_tokens,
            "pct_used":    pct,
            "cost_usd":    self.total_cost_usd,
            "message":     "OK",
        }

    # ── Usage recording ───────────────────────────────────────

    def record_usage(
        self,
        user_input:     str,
        agent_response: str,
        actual_tokens:  Optional[int] = None,
    ) -> int:
        """
        Record token usage AFTER a successful agent call.

        PILLAR 4 — COST CONTROLS (post-call accounting)

        Estimates tokens from input + response lengths if
        actual_tokens is not provided (e.g. when the OpenAI
        usage object is not forwarded to this layer).

        Args:
            user_input     (str): The user's original input.
            agent_response (str): The agent's final response.
            actual_tokens  (int): Actual tokens from OpenAI usage
                                  object, if available. Otherwise
                                  estimated automatically.

        Returns:
            int: Tokens used for this query.
        """
        if actual_tokens is not None:
            tokens = actual_tokens
        else:
            # Estimate: input + response + system prompt overhead (~500)
            tokens = _estimate_tokens(user_input) + \
                     _estimate_tokens(agent_response) + 500

        cost = tokens * COST_PER_TOKEN
        self.total_tokens   += tokens
        self.total_cost_usd += cost
        self.query_count    += 1

        # Log per-query detail for the cost breakdown table in the UI
        self._query_log.append({
            "query_num":    self.query_count,
            "query":        user_input[:60],
            "tokens":       tokens,
            "cost_usd":     cost,
            "cumulative":   self.total_tokens,
        })

        return tokens

    # ── Reporting ─────────────────────────────────────────────

    def get_summary(self) -> dict:
        """
        Return a full cost summary for the Governance Dashboard.

        PILLAR 4 — COST CONTROLS (dashboard reporting)

        Returns:
            dict: All session cost metrics for UI display.
        """
        budget_status = self.check_budget()
        return {
            "session_id":          self.session_id,
            "total_tokens":        self.total_tokens,
            "total_cost_usd":      round(self.total_cost_usd, 6),
            "query_count":         self.query_count,
            "state":               budget_status["state"],
            "pct_used":            round(budget_status["pct_used"], 1),
            "tokens_left":         budget_status["tokens_left"],
            "hard_stop_threshold": self.hard_stop_threshold,
            "warning_threshold":   self.warning_threshold,
            "query_log":           self._query_log.copy(),
            "session_age_sec":     round(time.time() - self._session_start),
        }

    def reset(self):
        """
        Reset all counters for a new session.
        Called when the user resets the chat conversation.
        """
        self.total_tokens   = 0
        self.total_cost_usd = 0.0
        self.query_count    = 0
        self._query_log     = []
        self._session_start = time.time()
