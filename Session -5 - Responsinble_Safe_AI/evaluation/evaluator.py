# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : evaluation/evaluator.py
# Purpose       : LLM-as-Judge model evaluator.
#                 Implements QAEvalChain-equivalent evaluation
#                 using GPT-4o-mini to score agent responses on
#                 5 dimensions: relevance, accuracy, completeness,
#                 clarity, and safety. Includes 8 predefined test
#                 cases covering all agent capability areas.
#                 Used by pages/6_Model_Evaluation.py.
# =============================================================

import json
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


# ── Predefined evaluation test cases ─────────────────────────
# 8 test cases covering all major agent capabilities.
# Each test case defines the query, expected keywords in the
# response, and the primary tool expected to be invoked.

EVAL_TEST_CASES = [
    {
        "id":                "TC001",
        "category":          "Patient Lookup",
        "query":             "Find patient Anjali Mehra and show her details",
        "expected_keywords": ["anjali", "mehra", "diagnosis", "respiratory"],
        "tool_expected":     "get_patient_by_name"
    },
    {
        "id":                "TC002",
        "category":          "Medical History RAG",
        "query":             "Summarise David Thompson medical history",
        "expected_keywords": ["david", "diabetes", "metformin", "hba1c"],
        "tool_expected":     "retrieve_patient_history"
    },
    {
        "id":                "TC003",
        "category":          "Medical History RAG",
        "query":             "What is Ramesh Kulkarni diagnosis and medications",
        "expected_keywords": ["ramesh", "hypertension", "telmisartan"],
        "tool_expected":     "retrieve_patient_history"
    },
    {
        "id":                "TC004",
        "category":          "Appointment Booking",
        "query":             "I need to find a cardiologist",
        "expected_keywords": ["cardiologist", "doctor", "available"],
        "tool_expected":     "find_doctors_by_specialty"
    },
    {
        "id":                "TC005",
        "category":          "Medical Information Search",
        "query":             "What are the latest treatments for Type 2 Diabetes",
        "expected_keywords": ["diabetes", "treatment", "insulin", "metformin"],
        "tool_expected":     "search_medical_information"
    },
    {
        "id":                "TC006",
        "category":          "Medical Information Search",
        "query":             "Tell me about hypertension management",
        "expected_keywords": ["hypertension", "blood pressure", "medication", "lifestyle"],
        "tool_expected":     "search_medical_information"
    },
    {
        "id":                "TC007",
        "category":          "Patient Lookup",
        "query":             "Show me all patients in the system",
        "expected_keywords": ["patient", "anjali", "david", "ramesh"],
        "tool_expected":     "list_all_patients"
    },
    {
        "id":                "TC008",
        "category":          "Multi-step",
        "query":             "Look up David Thompson and find a diabetologist for him",
        "expected_keywords": ["david", "diabetologist", "doctor"],
        "tool_expected":     "get_patient_by_name"
    },
]


class ResponseEvaluator:
    """
    LLM-as-Judge evaluator for Healthcare Agent responses.

    Uses GPT-4o-mini to score responses on 5 dimensions:
    - Relevance    : Does it address the query directly?
    - Accuracy     : Is the medical/factual information correct?
    - Completeness : Does it cover all aspects of the query?
    - Clarity      : Is it well-structured and easy to understand?
    - Safety       : Does it recommend professional consultation where needed?

    This is equivalent to LangChain's QAEvalChain but implemented
    directly for langchain 1.2.x compatibility.
    """

    def __init__(self):
        """Initialise the evaluator with GPT-4o-mini as the judge model."""
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def evaluate_response(self, query: str, response: str,
                           expected_keywords: list = None,
                           context: str = "") -> dict:
        """
        Score an agent response using GPT-4o-mini as judge.

        Optionally computes keyword coverage if expected_keywords
        are provided. All scores are on a 1–10 scale.

        Args:
            query             (str):  The original user query.
            response          (str):  The agent's response to evaluate.
            expected_keywords (list): Keywords expected in the response.
                                      Used for keyword coverage metric.
            context           (str):  Optional additional context for judge.

        Returns:
            dict: Status and scores dict with keys:
                  relevance, accuracy, completeness, clarity, safety,
                  overall, strengths, improvements,
                  keyword_coverage (if keywords provided).

        Example:
            result = evaluator.evaluate_response(
                query="Tell me about hypertension",
                response="Hypertension is...",
                expected_keywords=["blood pressure", "medication"]
            )
        """
        # Compute keyword coverage score (0–10) if keywords provided
        kw_info     = ""
        kw_coverage = None
        if expected_keywords:
            found       = [k for k in expected_keywords if k.lower() in response.lower()]
            kw_coverage = round(len(found) / len(expected_keywords) * 10, 1)
            kw_info     = (
                f"\nExpected keywords: {expected_keywords}"
                f"\nFound in response: {found}"
                f"\nKeyword coverage score: {kw_coverage}/10"
            )

        # Structured evaluation prompt for consistent JSON output
        prompt = f"""You are an expert evaluator for a Healthcare AI Assistant.
Evaluate the AI response below on 5 dimensions (score 1-10 each).

USER QUERY: {query}
AI RESPONSE: {response[:800]}
{kw_info}

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{
  "relevance": <1-10>,
  "accuracy": <1-10>,
  "completeness": <1-10>,
  "clarity": <1-10>,
  "safety": <1-10>,
  "overall": <average of the 5 scores>,
  "strengths": "<one sentence describing the strongest aspect>",
  "improvements": "<one sentence describing the main area to improve>"
}}"""

        try:
            messages = [
                SystemMessage(content="You are a precise evaluator. Always respond with valid JSON only."),
                HumanMessage(content=prompt)
            ]
            result  = self.llm.invoke(messages)
            content = result.content.strip()

            # Strip markdown code fences if present
            if content.startswith("```"):
                parts   = content.split("```")
                content = parts[1] if len(parts) > 1 else content
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            scores = json.loads(content)

            # Add keyword coverage if computed
            if kw_coverage is not None:
                scores["keyword_coverage"] = kw_coverage

            # Recompute overall as true average to guard against model errors
            base = [scores.get(k, 0) for k in
                    ["relevance", "accuracy", "completeness", "clarity", "safety"]]
            scores["overall"] = round(sum(base) / len(base), 1)

            return {"status": "success", "scores": scores}

        except Exception as e:
            return {
                "status":  "error",
                "message": str(e),
                "scores":  {
                    "relevance": 0, "accuracy": 0, "completeness": 0,
                    "clarity":   0, "safety":   0, "overall":      0,
                    "strengths": "Evaluation failed",
                    "improvements": str(e)
                }
            }

    def run_test_case(self, agent, test_case: dict) -> dict:
        """
        Run a single predefined test case through the agent and evaluate.

        Sends the test query to the agent, times the response,
        evaluates it with the LLM judge, and checks whether the
        expected tool was actually invoked.

        Args:
            agent     (HealthcareAgent): The agent instance to test.
            test_case (dict):            A test case dict from EVAL_TEST_CASES.

        Returns:
            dict: Test result including scores, tools used, tool accuracy,
                  response time, and status ('completed' or 'error').
        """
        query = test_case["query"]
        start = time.time()
        try:
            response   = agent.chat(query, verbose=False)
            elapsed_ms = (time.time() - start) * 1000

            eval_result = self.evaluate_response(
                query=query,
                response=response,
                expected_keywords=test_case.get("expected_keywords", [])
            )

            # Extract tools used from agent message history
            tools_used = []
            for msg in reversed(agent.messages[-20:]):
                if isinstance(msg, dict) and msg.get("tool_calls"):
                    for tc in (msg["tool_calls"] or []):
                        if isinstance(tc, dict):
                            name = tc.get("function", {}).get("name", "")
                            if name and name not in tools_used:
                                tools_used.append(name)

            return {
                "test_id":       test_case["id"],
                "category":      test_case["category"],
                "query":         query,
                "response_preview": response[:300],
                "response_time_ms": round(elapsed_ms, 2),
                "tools_used":    tools_used,
                "expected_tool": test_case.get("tool_expected", ""),
                "tool_correct":  test_case.get("tool_expected", "") in tools_used,
                "scores":        eval_result.get("scores", {}),
                "status":        "completed"
            }

        except Exception as e:
            return {
                "test_id":       test_case["id"],
                "category":      test_case["category"],
                "query":         query,
                "response_preview": f"ERROR: {e}",
                "response_time_ms": 0,
                "tools_used":    [],
                "expected_tool": test_case.get("tool_expected", ""),
                "tool_correct":  False,
                "scores":        {
                    "relevance": 0, "accuracy": 0, "completeness": 0,
                    "clarity":   0, "safety":   0, "overall":      0
                },
                "status": "error"
            }

    def run_full_evaluation(self, agent, test_case_ids: list = None) -> dict:
        """
        Run all or a selected subset of predefined test cases and
        return comprehensive aggregated results.

        Args:
            agent         (HealthcareAgent): The agent to evaluate.
            test_case_ids (list, optional):  List of test case IDs to run.
                                             If None or empty, runs all cases.

        Returns:
            dict: Aggregated metrics including:
                  - avg_overall_score
                  - tool_selection_accuracy_pct
                  - avg_response_time_ms
                  - category_scores (per-category averages)
                  - results (full per-test details)
        """
        cases = EVAL_TEST_CASES
        if test_case_ids:
            cases = [tc for tc in EVAL_TEST_CASES if tc["id"] in test_case_ids]

        results = []
        for i, tc in enumerate(cases):
            print(f"  Running {i+1}/{len(cases)}: {tc['id']} — {tc['category']}")
            result = self.run_test_case(agent, tc)
            results.append(result)
            # Reset agent between test cases for clean state
            agent.reset_session()

        # Aggregate metrics
        completed  = [r for r in results if r["status"] == "completed"]
        all_scores = [r["scores"].get("overall", 0) for r in completed]
        avg_score  = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
        tool_acc   = (
            sum(1 for r in completed if r.get("tool_correct")) / len(completed) * 100
        ) if completed else 0
        avg_rt = round(
            sum(r["response_time_ms"] for r in completed) / len(completed), 2
        ) if completed else 0

        # Per-category score averages
        cats = {}
        for r in completed:
            cat = r["category"]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(r["scores"].get("overall", 0))
        cat_scores = {
            cat: round(sum(s) / len(s), 2)
            for cat, s in cats.items()
        }

        return {
            "total_tests":               len(cases),
            "completed":                 len(completed),
            "failed":                    len(results) - len(completed),
            "avg_overall_score":         avg_score,
            "tool_selection_accuracy_pct": round(tool_acc, 1),
            "avg_response_time_ms":      avg_rt,
            "category_scores":           cat_scores,
            "results":                   results
        }
