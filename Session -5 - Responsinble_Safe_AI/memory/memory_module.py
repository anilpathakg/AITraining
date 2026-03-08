# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : memory/memory_module.py
# Purpose       : Conversation memory and patient context manager.
#                 Implements a sliding window conversation buffer
#                 that retains the last N interaction turns, plus
#                 a separate patient context store that tracks the
#                 currently active patient across multi-turn chats.
#                 Does NOT use LangChain's ConversationBufferMemory
#                 (removed in langchain 1.2.x) — uses plain Python.
# =============================================================

from typing import Optional


class HealthcareMemory:
    """
    Manages two types of memory for the Healthcare Agent:

    1. Conversation Window: A sliding buffer of the last `window_size`
       user/assistant interaction pairs. Older turns are dropped to
       keep the context window manageable.

    2. Patient Context: A dictionary storing the currently active
       patient's record (set when a patient is looked up). This is
       injected into the agent system prompt so the agent is always
       aware of who it is assisting without needing to re-fetch.

    Attributes:
        window_size    (int):  Max number of interaction turns to retain.
        _conversation  (list): List of {role, content} turn dicts.
        _patient_ctx   (dict): Active patient record, or empty dict.
    """

    def __init__(self, window_size: int = 10):
        """
        Initialise the memory module.

        Args:
            window_size (int): Number of conversation turns to keep in
                               the sliding window. Default is 10.
        """
        self.window_size   = window_size
        self._conversation = []   # Sliding window of turns
        self._patient_ctx  = {}   # Active patient context

    # ── Conversation memory ───────────────────────────────────

    def add_interaction(self, user_input: str, assistant_response: str):
        """
        Add a completed interaction turn to the conversation window.
        Drops the oldest turn if the window size is exceeded.

        Args:
            user_input         (str): The user's message.
            assistant_response (str): The agent's response.
        """
        self._conversation.append({
            "role":    "user",
            "content": user_input
        })
        self._conversation.append({
            "role":    "assistant",
            "content": assistant_response
        })

        # Enforce sliding window — keep only the last N pairs
        # Each pair = 2 entries (user + assistant)
        max_entries = self.window_size * 2
        if len(self._conversation) > max_entries:
            self._conversation = self._conversation[-max_entries:]

    def get_conversation_history(self) -> list:
        """
        Return the current conversation window as a list of
        {role, content} dicts suitable for the OpenAI messages format.

        Returns:
            list: Conversation turns in chronological order.
        """
        return self._conversation.copy()

    def clear_conversation(self):
        """Clear all conversation history. Called on session reset."""
        self._conversation = []

    # ── Patient context ───────────────────────────────────────

    def set_patient_context(self, patient: dict):
        """
        Set the active patient context. Called automatically by the
        agent when a patient lookup tool returns a successful result.

        Args:
            patient (dict): Patient record dict from patient_db_tool.
        """
        self._patient_ctx = patient

    def get_patient_context(self) -> dict:
        """
        Return the currently active patient context dictionary.

        Returns:
            dict: Patient record, or empty dict if no patient is active.
        """
        return self._patient_ctx.copy()

    def get_patient_context_string(self) -> str:
        """
        Format the active patient context as a human-readable string
        for injection into the agent system prompt.

        Returns:
            str: Formatted patient summary, or a message indicating
                 no patient is currently active.
        """
        if not self._patient_ctx:
            return "No patient currently active. Ask the user for a patient name if needed."

        lines = ["Currently active patient:"]
        for k, v in self._patient_ctx.items():
            val = str(v).strip()
            if val and val not in ["N/A", "nan", "None", ""]:
                lines.append(f"  {k}: {val}")
        return "\n".join(lines)

    def clear_patient_context(self):
        """Clear the active patient context. Called on session reset."""
        self._patient_ctx = {}

    # ── Utility ───────────────────────────────────────────────

    def get_summary(self) -> dict:
        """
        Return a summary of current memory state for debugging.

        Returns:
            dict: Turn count, window size, and whether a patient is active.
        """
        return {
            "conversation_turns": len(self._conversation) // 2,
            "window_size":        self.window_size,
            "patient_active":     bool(self._patient_ctx),
            "patient_name":       self._patient_ctx.get("Name",
                                  self._patient_ctx.get("name", "None"))
        }
