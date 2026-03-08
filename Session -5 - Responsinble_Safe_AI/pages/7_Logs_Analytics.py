# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : pages/7_Logs_Analytics.py
# Purpose       : Doctor/Admin Section — Logs and Analytics.
#                 Real-time monitoring dashboard showing agent
#                 interaction logs, tool usage frequency, booking
#                 success rates, evaluation scores, and per-module
#                 performance metrics.
# =============================================================

import streamlit as st
import pandas as pd
import json, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sidebar_helper import render_sidebar


from evaluation.logger import get_all_logs, get_logs_by_type, get_analytics_summary, clear_logs

st.set_page_config(page_title="Logs & Analytics", page_icon="bar_chart", layout="wide")

# Set role for contextual sidebar
st.session_state["role"] = "admin"
render_sidebar()

st.title("Logs & Analytics")
st.caption("Real-time monitoring of agent interactions, tool usage, and performance metrics")
st.divider()

col_r, col_c, _ = st.columns([1,1,4])
with col_r:
    if st.button("Refresh", width='stretch'): st.rerun()
with col_c:
    if st.button("Clear Logs", width='stretch', type="secondary"):
        clear_logs(); st.success("Logs cleared."); st.rerun()

summary = get_analytics_summary()

st.subheader("Overview Metrics")
m1,m2,m3,m4,m5,m6 = st.columns(6)
m1.metric("Total Interactions", summary["total_interactions"])
m2.metric("Total Tool Calls", summary["total_tool_calls"])
m3.metric("Total Evaluations", summary["total_evaluations"])
m4.metric("Avg Response Time", f"{summary['avg_response_time_ms']}ms")
m5.metric("Avg Eval Score", f"{summary['avg_evaluation_score']}/10")
m6.metric("Booking Success", f"{summary.get('booking_success_rate_pct', 0)}%")

# Booking module metrics
st.divider()
st.subheader("Appointment Booking Module Performance")
bc1, bc2, bc3 = st.columns(3)
bc1.metric("Total Booking Attempts", summary.get("booking_total", 0))
bc2.metric("Successful Bookings", summary.get("booking_success", 0))
bc3.metric("Booking Success Rate", f"{summary.get('booking_success_rate_pct', 0)}%",
           delta="Target: 95%+",
           delta_color="normal" if summary.get("booking_success_rate_pct", 0) >= 95 else "inverse")

st.divider()
tab1,tab2,tab3,tab4 = st.tabs(["Tool Usage","Interaction Logs","Evaluation Logs","Raw Logs"])

with tab1:
    st.subheader("Tool Usage Analytics")
    tool_freq = summary.get("tool_usage_frequency", {})
    tool_sr = summary.get("tool_success_rates", {})

    if tool_freq:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Tool Call Frequency**")
            freq_df = pd.DataFrame([{"Tool":k,"Calls":v} for k,v in sorted(tool_freq.items(), key=lambda x:x[1], reverse=True)])
            st.bar_chart(freq_df.set_index("Tool"))
        with c2:
            st.markdown("**Tool Success Rate (%)**")
            sr_df = pd.DataFrame([{"Tool":k,"Success Rate (%)":v} for k,v in sorted(tool_sr.items(), key=lambda x:x[1], reverse=True)])
            st.bar_chart(sr_df.set_index("Tool"))

        st.markdown("**Combined Tool Statistics**")
        combined = [{"Tool":t, "Total Calls":tool_freq.get(t,0), "Success Rate (%)":tool_sr.get(t,0)} for t in tool_freq]
        st.dataframe(pd.DataFrame(combined), width='stretch')
        st.info(f"Most Used Tool: **{summary.get('most_used_tool','N/A')}**")

        # Per-module success breakdown
        st.markdown("**Module Performance Breakdown**")
        modules = {
            "Patient Lookup": ["get_patient_by_name","get_patient_by_id","list_all_patients"],
            "Appointment Booking": ["find_doctors_by_specialty","get_available_slots_for_doctor","book_appointment","cancel_appointment"],
            "Medical History RAG": ["retrieve_patient_history","search_across_all_patients"],
            "Medical Search": ["search_medical_information","get_disease_overview","get_drug_information"],
            "Record Management": ["update_patient_record","add_patient_record"]
        }
        module_stats = []
        for module, tools in modules.items():
            calls = sum(tool_freq.get(t, 0) for t in tools)
            success = sum(tool_sr.get(t, 0) * tool_freq.get(t, 0) / 100 for t in tools if tool_freq.get(t, 0) > 0)
            rate = round(success / calls * 100, 1) if calls > 0 else 0
            module_stats.append({"Module": module, "Total Calls": calls, "Avg Success Rate (%)": rate})
        st.dataframe(pd.DataFrame(module_stats), width='stretch')
    else:
        st.info("No tool usage data yet. Start chatting with the agent to generate data.")

with tab2:
    st.subheader("Interaction Logs")
    interactions = get_logs_by_type("interaction")
    if interactions:
        times_data = pd.DataFrame([{"#":i+1,"Response Time (ms)":l.get("response_time_ms",0),"Tools Used":l.get("tool_count",0)} for i,l in enumerate(interactions)])
        st.line_chart(times_data.set_index("#")[["Response Time (ms)"]])
        table = [{"Timestamp":l.get("timestamp","")[:19], "Session":l.get("session_id",""),"User Input":l.get("user_input","")[:60],"Tools":", ".join(l.get("tools_used",[])),"Time (ms)":l.get("response_time_ms",0)} for l in reversed(interactions[-50:])]
        st.dataframe(pd.DataFrame(table), width='stretch')
        st.subheader("Agent Memory Traces")
        for log in reversed(interactions[-5:]):
            with st.expander(f"{log.get('timestamp','')[:19]} | {log.get('user_input','')[:50]}"):
                st.markdown(f"**Input:** {log.get('user_input','')}")
                st.markdown(f"**Tools:** {', '.join(log.get('tools_used',[])) or 'None'}")
                st.markdown(f"**Response:** {log.get('agent_response','')[:400]}")
                st.caption(f"Session: {log.get('session_id','')} | Time: {log.get('response_time_ms',0)}ms")
    else:
        st.info("No interaction logs yet.")

with tab3:
    st.subheader("Evaluation Logs")
    evals = get_logs_by_type("evaluation")
    if evals:
        rows = []
        for e in reversed(evals[-30:]):
            sc = e.get("scores",{})
            rows.append({"Timestamp":e.get("timestamp","")[:19],"Query":e.get("query","")[:50],"Relevance":sc.get("relevance",0),"Accuracy":sc.get("accuracy",0),"Completeness":sc.get("completeness",0),"Clarity":sc.get("clarity",0),"Safety":sc.get("safety",0),"Overall":sc.get("overall",0)})
        df = pd.DataFrame(rows)
        st.dataframe(df, width='stretch')
        if len(df) > 1:
            st.subheader("Score Trends")
            st.line_chart(df[["Relevance","Accuracy","Completeness","Clarity","Safety","Overall"]])
    else:
        st.info("No evaluation logs yet. Run evaluations from the Model Evaluation page.")

with tab4:
    st.subheader("Raw Log Viewer")
    all_logs = get_all_logs()
    if all_logs:
        ltype = st.selectbox("Filter by type", ["all","interaction","tool_call","evaluation"])
        filtered = all_logs if ltype=="all" else [l for l in all_logs if l.get("type")==ltype]
        st.caption(f"Showing {min(50,len(filtered))} of {len(filtered)} logs")
        for log in reversed(filtered[-50:]):
            label = log.get("tool_name",log.get("user_input",log.get("query","")))
            with st.expander(f"[{log.get('type','').upper()}] {log.get('timestamp','')[:19]} | {str(label)[:50]}"):
                st.json(log)
    else:
        st.info("No logs available yet.")
