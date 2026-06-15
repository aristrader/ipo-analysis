import streamlit as st
import json
from dotenv import load_dotenv
import os

# Ensure API keys are loaded
load_dotenv()

# We need to import our nodes. Since we are in the orchestration folder, we can just import them.
# To make it robust if run from root directory, we use absolute imports if possible
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
sys.path.append(str(ROOT_DIR))

from thinktank.orchestration.nodes import (
    step0_triage_history,
    step1_high_ideation,
    step1_5_review_agent,
    step2_execution_planning,
    step3_code_generation,
    step4_peer_review
)

st.set_page_config(page_title="Think Tank Control Center", layout="wide")
st.title("🧠 Think Tank Control Center")

if "pipeline_state" not in st.session_state:
    st.session_state["pipeline_state"] = {}

seed_idea = st.text_input("Enter your Seed Hypothesis:")

if st.button("Run Ideation"):
    with st.spinner("Triaging and Exploding Hypotheses..."):
        state = {"task_description": seed_idea, "messages": [], "errors": []}
        state.update(step0_triage_history(state))
        state.update(step1_high_ideation(state))
        state.update(step1_5_review_agent(state))
        st.session_state["pipeline_state"] = state
        st.rerun()

state = st.session_state.get("pipeline_state", {})

if "sorted_ideas" in state:
    if "execution_plan" not in state:
        st.subheader("Checkpoint 1: Pruning & Expansion")
    else:
        st.subheader("Checkpoint 1: Pruning & Expansion (Completed)")
        
    # Put Checkpoint 1 in an expander if we've moved past it, otherwise keep it open
    with st.expander("View Hypotheses Grid", expanded=("execution_plan" not in state)):
        st.markdown("### Prior Art Report:")
        st.info(state.get("prior_art_report", "No prior art found."))
        
        st.markdown("### Ideation Results:")
        
        # Parse the sorted ideas
        sorted_ideas_str = state.get("sorted_ideas", "[]")
        if sorted_ideas_str.startswith("```json"):
            sorted_ideas_str = sorted_ideas_str[7:]
        if sorted_ideas_str.endswith("```"):
            sorted_ideas_str = sorted_ideas_str[:-3]
            
        try:
            import json
            ideas_list = json.loads(sorted_ideas_str.strip())
            
            final_approved = []
            deferred_high = []
            deferred_low = []
            has_open = False
            for i, item in enumerate(ideas_list):
                col1, col2, col3 = st.columns([3, 4, 1])
                with col1:
                    st.write(item.get("idea", "Unknown"))
                with col2:
                    st.write(item.get("justification", "No reason provided."))
                with col3:
                    # If already executed, make it read-only text, otherwise a selectbox
                    status = item.get("status", "OPEN").upper()
                    if "execution_plan" in state:
                        st.write(f"**{status}**")
                    else:
                        options = ["IN", "CUT", "OPEN", "DEFER (High)", "DEFER (Low)"]
                        idx = 0
                        if status == "CUT": idx = 1
                        elif status == "OPEN": idx = 2
                        choice = st.selectbox("Status", options, index=idx, key=f"status_{i}")
                        if choice == "OPEN":
                            has_open = True
                        elif choice == "IN":
                            final_approved.append(item.get("idea"))
                        elif choice == "DEFER (High)":
                            deferred_high.append(item.get("idea"))
                        elif choice == "DEFER (Low)":
                            deferred_low.append(item.get("idea"))
            
            if "execution_plan" not in state:
                if has_open:
                    st.warning("⚠️ You must resolve all 'OPEN' items to either 'IN', 'CUT', or 'DEFER' before proceeding.")
                elif st.button("Confirm & Build Plan"):
                    with st.spinner("Saving Deferred Items & Generating Execution Plan (Autonomous Loop)..."):
                        # Save deferred items to their respective backlogs
                        if deferred_high:
                            with open(ROOT_DIR / "docs" / "research" / "backlog" / "deferred_high.md", "a") as f:
                                for idea in deferred_high:
                                    f.write(f"- {idea}\n\n")
                        if deferred_low:
                            with open(ROOT_DIR / "docs" / "research" / "backlog" / "deferred_low.md", "a") as f:
                                for idea in deferred_low:
                                    f.write(f"- {idea}\n\n")

                        state["approved_ideas"] = "\n".join(final_approved)
                        
                        from thinktank.orchestration.nodes import step2_execution_planning, step3_code_generation, step4_peer_review, step4_5_final_judge
                        state.update(step2_execution_planning(state))
                        
                        state["execution_history"] = []
                        state["human_directives"] = ""
                        state["prior_swarm_feedback"] = ""
                        state["human_retry_count"] = 0
                        
                        # Autonomous Inner Loop (Max 2)
                        for i in range(2):
                            state.update(step3_code_generation(state))
                            state.update(step4_peer_review(state))
                            state.update(step4_5_final_judge(state))
                            
                            state["execution_history"].append({
                                "run": len(state["execution_history"]) + 1,
                                "code": state.get("code_execution_result", ""),
                                "feedback": state.get("peer_review_feedback", ""),
                                "verdict": state.get("swarm_verdict", "FAIL")
                            })
                            
                            if state.get("swarm_verdict") == "PASS":
                                break
                            
                            state["prior_swarm_feedback"] = state.get("peer_review_feedback", "")
                        
                        st.session_state["pipeline_state"] = state
                        st.rerun()
                    
        except Exception as e:
            st.error(f"Failed to parse Review Agent JSON: {e}")
            st.text(state["sorted_ideas"])

if "execution_plan" in state:
    st.markdown("---")
    st.subheader("Checkpoint 2: Execution & Review")
    
    with st.expander("Approved Hypotheses Sent to Execution", expanded=False):
        for idea in state.get("approved_ideas", "").split("\n"):
            if idea.strip():
                st.success(f"✓ {idea}")
                
    history = state.get("execution_history", [])
    if history:
        st.markdown("### Execution History")
        tabs = st.tabs([f"Run {h['run']} ({h['verdict']})" for h in history])
        for idx, tab in enumerate(tabs):
            with tab:
                st.markdown("**Generated Code**")
                st.code(history[idx]['code'], language="python")
                st.markdown("**Peer Review Feedback**")
                st.info(history[idx]['feedback'])
                
    st.markdown("---")
    st.markdown("### Human Interaction Layer")
    
    issues = state.get("unresolved_issues", [])
    if state.get("swarm_verdict") == "PASS":
        st.success("The Swarm passed the code! You can proceed to Record Verdict.")
        if issues:
            with st.expander("Minor notes from the Swarm (optional review)"):
                for issue in issues:
                    st.info(f"Issue {issue['id']}: {issue['description']}")
    else:
        retry_count = state.get("human_retry_count", 0)
        st.warning(f"The Swarm flagged issues. (Human interventions so far: {retry_count})")
        
        human_inputs = []
        if issues:
            st.markdown("**Unresolved Issues (Provide Directives):**")
            for issue in issues:
                response = st.text_input(f"Issue {issue['id']}: {issue['description']}", key=f"dir_{issue['id']}_{retry_count}")
                if response:
                    human_inputs.append(f"Issue {issue['id']} Directive: {response}")
                
        if st.button("Refine & Retry"):
            with st.spinner("Self-Correcting based on your directives..."):
                state["human_directives"] = "\n".join(human_inputs) if human_inputs else "Please fix remaining issues."
                state["prior_swarm_feedback"] = state.get("peer_review_feedback", "")
                
                from thinktank.orchestration.nodes import step3_code_generation, step4_peer_review, step4_5_final_judge
                
                # Human-directed inner loop (2 autonomous attempts per click)
                for i in range(2):
                    state.update(step3_code_generation(state))
                    state.update(step4_peer_review(state))
                    state.update(step4_5_final_judge(state))
                    
                    state["execution_history"].append({
                        "run": len(state["execution_history"]) + 1,
                        "code": state.get("code_execution_result", ""),
                        "feedback": state.get("peer_review_feedback", ""),
                        "verdict": state.get("swarm_verdict", "FAIL")
                    })
                    
                    if state.get("swarm_verdict") == "PASS":
                        break
                    
                    state["prior_swarm_feedback"] = state.get("peer_review_feedback", "")
                    state["human_directives"] = ""
                    
                state["human_retry_count"] = retry_count + 1
                st.session_state["pipeline_state"] = state
                st.rerun()

    st.markdown("---")
    st.markdown("### Final Decision")
    verdict = st.radio("Final Verdict:", ["PASS", "REJECT", "NEEDS REVISION"])
    if st.button("Record Verdict"):
        with st.spinner("Writing Dossier and Updating Task Log..."):
            from thinktank.orchestration.nodes import step7_record
            state["final_verdict"] = verdict
            res = step7_record(state)
            st.success(f"Verdict recorded: {verdict}. Dossier saved to: {res.get('dossier_path')}")
            st.info("The docs/research/task_log.md has also been updated.")
