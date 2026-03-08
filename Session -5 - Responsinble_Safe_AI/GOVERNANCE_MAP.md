# Governance Map — V4 Healthcare Assistant
## IEEE Session 5: Responsible & Safe Agentic AI Systems

> **How to use this file:**  
> Keep this open alongside the code.  
> Each row maps a governance concept → the file that implements it → the function to look for.  
> In VS Code: search for `[V4 · PILLAR N]` in any file to jump to that pillar's code.

---

## The 5 Pillars

| # | Pillar | What it does | Primary file | Key function/class |
|---|--------|-------------|--------------|-------------------|
| 1 | 🛡️ Safety Guardrails | Blocks PII & harmful queries before LLM; adds safety footer to risky outputs | `governance/guardrails.py` | `input_guardrail()` `output_guardrail()` |
| 2 | 📊 Evaluation | Scores every chat response on 5 dimensions using LLM-as-judge | `evaluation/evaluator.py` (V3, unwired) → `pages/8_Chat_Assistant.py` (V4 wiring) | `ResponseEvaluator.evaluate_response()` |
| 3 | 📝 Audit Log | Persists every governance event with timestamp, risk level, PII flag, decision | `evaluation/logger.py` | `log_governance_event()` ← NEW in V4 |
| 4 | 💰 Cost Controls | Tracks session tokens, enforces WARNING and HARD_STOP budget thresholds | `governance/cost_controller.py` | `CostController` class |
| 5 | 👤 Human-in-the-Loop | Intercepts HIGH RISK tools, pauses agent, waits for human Approve/Reject/Edit | `governance/hitl_manager.py` | `classify_risk()` `HITLInterrupt` |

---

## Where Each Pillar Touches the Code

### Pillar 1 — Safety Guardrails
```
governance/guardrails.py         ← ALL guardrail logic lives here
    input_guardrail(text)        ← Stage 1: called in agent.chat() BEFORE LLM
    output_guardrail(text)       ← Stage 2: called in agent.chat() AFTER LLM
    mask_pii(text)               ← Used before writing to audit log

agent.py                         ← [V4 · PILLAR 1] markers show wiring points
    Line ~160: input_guardrail() called, BLOCK → return safe_message
    Line ~240: output_guardrail() called, risky output → append footer
```

### Pillar 2 — Evaluation
```
evaluation/evaluator.py          ← V3 UNCHANGED — ResponseEvaluator class
    evaluate_response(q, r)      ← GPT-4o-mini as judge, 5 dimensions

pages/8_Chat_Assistant.py        ← [V4 · PILLAR 2] wiring NEW in V4
    After every agent response:  ResponseEvaluator().evaluate_response()
    Score shown as ⭐ badge in chat
    Logged via log_governance_event(event_type="EVAL_SCORED")
```

### Pillar 3 — Audit Log
```
evaluation/logger.py             ← V3 base + V4 additions
    log_interaction()            ← V3 UNCHANGED
    log_tool_call()              ← V3 UNCHANGED
    log_evaluation()             ← V3 UNCHANGED
    log_governance_event()       ← NEW in V4 — the governance audit trail
    get_governance_logs()        ← NEW in V4 — read governance events
    get_governance_summary()     ← NEW in V4 — aggregated counts for dashboard

pages/9_AI_Governance.py        ← NEW in V4 — the governance dashboard UI
    Uses get_governance_logs() and get_governance_summary()
```

### Pillar 4 — Cost Controls
```
governance/cost_controller.py   ← NEW in V4 — entire file
    CostController               ← Session-scoped budget tracker
        check_budget()           ← Called BEFORE every LLM call
        record_usage()           ← Called AFTER every LLM response
        get_summary()            ← Called by Governance Dashboard

agent.py                        ← [V4 · PILLAR 4] markers show wiring
    self.cost_controller = CostController(...)   ← created in __init__
    budget = self.cost_controller.check_budget() ← gate in chat()
    self.cost_controller.record_usage(...)       ← accounting in chat()
    self.cost_controller.reset()                 ← called in reset_session()
```

### Pillar 5 — Human-in-the-Loop
```
governance/hitl_manager.py      ← NEW in V4 — entire file
    TOOL_RISK_LEVELS             ← dict: tool_name → "HIGH" | "LOW"
    classify_risk(tool, args)    ← returns "HIGH" or "LOW"
    HITLInterrupt                ← exception raised for HIGH RISK tools
    build_hitl_pending(...)      ← builds the dict stored in session_state

agent.py                        ← [V4 · PILLAR 5] markers show wiring
    BEFORE dispatch_tool():      risk = classify_risk(tool_name, tool_args)
    If HIGH:                     raise HITLInterrupt(tool_name, tool_args)
    New method:                  execute_approved_hitl_action()

pages/8_Chat_Assistant.py       ← [V4 · PILLAR 5] approval widget
    Catches HITLInterrupt        ← stores pending in st.session_state
    Renders Approve/Reject/Edit  ← disables chat input while pending
    Calls execute_approved_hitl_action() on approve
```

---

## V3 vs V4 File Status

| File | Status | Notes |
|------|--------|-------|
| `governance/__init__.py` | 🆕 NEW | Package init |
| `governance/guardrails.py` | 🆕 NEW | Pillar 1 |
| `governance/cost_controller.py` | 🆕 NEW | Pillar 4 |
| `governance/hitl_manager.py` | 🆕 NEW | Pillar 5 |
| `pages/9_AI_Governance.py` | 🆕 NEW | Governance Dashboard UI |
| `agent.py` | ✏️ MODIFIED | All 5 pillars wired in |
| `evaluation/logger.py` | ✏️ MODIFIED | `log_governance_event()` added |
| `utils/sidebar_helper.py` | ✏️ MODIFIED | Governance link added |
| `pages/0_Doctor_Dashboard.py` | ✏️ MODIFIED | Governance card added |
| `pages/8_Chat_Assistant.py` | ✏️ MODIFIED | Pillars 1,2,4,5 wired in UI |
| All other files | ✅ UNCHANGED | V3 code preserved exactly |

---

## Search Tags (use Ctrl+F in any file)

| Search for | Finds |
|------------|-------|
| `[V4 · PILLAR 1` | All Guardrail wiring points |
| `[V4 · PILLAR 2` | All Evaluation wiring points |
| `[V4 · PILLAR 3` | All Audit Log wiring points |
| `[V4 · PILLAR 4` | All Cost Control wiring points |
| `[V4 · PILLAR 5` | All HITL wiring points |
| `BEFORE V4` | Shows what the V3 code did at each point |
| `AFTER  V4` | Shows what V4 does instead |
| `V3 — UNCHANGED` | Confirms a section was not modified |

---

*Anil Pathak's Agentic Healthcare Assistant · V4 · IEEE Session 5*
