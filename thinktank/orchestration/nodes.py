import os
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from thinktank.orchestration.state import ThinkTankState

ROOT_DIR = Path(__file__).parent.parent.parent.resolve()

def get_llm():
    model_name = os.environ.get("THINKTANK_MODEL", "gemini-3.1-flash-lite")
    return ChatGoogleGenerativeAI(model=model_name)

def _extract_text(content):
    if isinstance(content, list) and len(content) > 0 and isinstance(content[0], dict):
        return content[0].get("text", str(content))
    return str(content)

def step0_triage_history(state: ThinkTankState) -> dict:
    task = state.get("task_description", "")
    print(f"\n[Step 0] Triaging Task: {task}")
    llm = get_llm()
    sys_prompt = SystemMessage(content="You are the Triage Agent. State if the task is novel.\n"
        "CRITICAL: If the hypothesis is based on a logically impossible causal mechanism (e.g., a company's name length physically affecting its stock price), you MUST flag this as 'LOGICALLY SUSPECT' and explain why, even if the task is technically novel.")
    user_prompt = HumanMessage(content=f"Task: {task}")
    response = llm.invoke([sys_prompt, user_prompt])
    return {"prior_art_report": _extract_text(response.content), "messages": [response]}

def step1_high_ideation(state: ThinkTankState) -> dict:
    task = state.get("task_description", "")
    print("\n[Step 1] Exploding seed idea into chained hypotheses...")
    llm = get_llm() 
    sys_prompt = SystemMessage(content="You are the Ideation Agent. Transform the seed thought into 10-15 detailed hypotheses.\n"
        "For each hypothesis, write a rich, multi-sentence paragraph detailing:\n"
        "1. The exact mathematical/statistical mechanism to be tested.\n"
        "2. The specific market data fields required.\n"
        "3. Why this specific angle provides unique alpha or insight.\n"
        "Do not be brief. Provide highly rigorous, detailed proposals.")
    user_prompt = HumanMessage(content=f"Seed: {task}")
    response = llm.invoke([sys_prompt, user_prompt])
    return {"raw_ideas": _extract_text(response.content), "messages": [response]}

def step1_5_review_agent(state: ThinkTankState) -> dict:
    raw_ideas = state.get("raw_ideas", "")
    print("\n[Step 1.5] Automated Review Agent sorting ideas...")
    llm = get_llm()
    sys_prompt = SystemMessage(content="You are the Review Agent. You decide which ideas live or die.\n"
        "1. For each idea, output IN or CUT with a 1-sentence reason.\n"
        "2. Keep ONLY if highly valuable and mathematically testable with standard market data.\n"
        "3. THE PROXY TEST: Actively check if the hypothesis is a spurious correlation or proxy for a confounding variable (e.g., sector, market cap, issue size). If the proposed signal is likely just a noisy proxy for a known factor, mark it CUT.\n"
        "Mark generic, duplicate, or impossible ideas as 'CUT'. Leave borderline ideas as 'OPEN'. You must be critical and try to CUT weak ideas.\n"
        "IMPORTANT: You must return the result as a raw JSON array of objects. Do NOT wrap it in markdown block quotes (like ```json).\n"
        "Format: [{\"idea\": \"DETAILED hypothesis title and full mathematical explanation from the prompt\", \"status\": \"IN\"|\"CUT\"|\"OPEN\", \"justification\": \"detailed reason for decision\"}]")
    user_prompt = HumanMessage(content=f"Raw Ideas:\n{raw_ideas}")
    response = llm.invoke([sys_prompt, user_prompt])
    return {"sorted_ideas": _extract_text(response.content), "messages": [response]}

def human_checkpoint_1(state: ThinkTankState) -> dict:
    sorted_ideas = state.get("sorted_ideas", "")
    print("\n" + "="*50)
    print("⏸️ HUMAN CHECKPOINT 1: Review & Prune Hypotheses")
    print("="*50)
    print(f"\n{sorted_ideas}\n")
    # Simulation input
    approved = input("Enter approved hypotheses to carry forward (or 'skip'): ")
    if approved.strip().lower() == 'skip':
        approved = "Default approved hypotheses"
    return {"approved_ideas": approved}

def step2_execution_planning(state: ThinkTankState) -> dict:
    approved = state.get("approved_ideas", "")
    print("\n[Step 2] Execution Planning (Codebase-Grounded)...")
    llm = get_llm()
    
    # Read key files and inject as context
    try:
        spine_content = (ROOT_DIR / "layer3" / "spine.py").read_text()
    except Exception:
        spine_content = "File layer3/spine.py not found."
        
    try:
        config_content = (ROOT_DIR / "layer3" / "config.py").read_text()
    except Exception:
        config_content = "File layer3/config.py not found."
        
    try:
        schema_content = (ROOT_DIR / "docs" / "schema.md").read_text()
    except Exception:
        schema_content = "File docs/schema.md not found."
        
    prompt = "You are the Planning Agent. Write a mathematical execution plan for testing these hypotheses using Python and Pandas.\n\n"
    prompt += "CRITICAL INSTRUCTIONS:\n"
    prompt += "1. You MUST use the existing codebase helpers defined below.\n"
    prompt += "2. Do NOT reinvent helpers that already exist in spine.py.\n"
    prompt += "3. Use the exact column names from the data schema.\n"
    prompt += "4. Do NOT import scipy or statsmodels (they are banned). Use pure python math or pandas.\n\n"
    prompt += f"--- AVAILABLE HELPERS (spine.py) ---\n{spine_content}\n\n"
    prompt += f"--- CONSTANTS (config.py) ---\n{config_content}\n\n"
    prompt += f"--- DATA SCHEMA (schema.md) ---\n{schema_content}\n"
    
    sys_prompt = SystemMessage(content=prompt)
    user_prompt = HumanMessage(content=f"Approved Ideas: {approved}")
    response = llm.invoke([sys_prompt, user_prompt])
    return {"execution_plan": _extract_text(response.content), "messages": [response]}

def step3_code_generation(state: ThinkTankState) -> dict:
    plan = state.get("execution_plan", "")
    prior_feedback = state.get("prior_swarm_feedback", "")
    human_directives = state.get("human_directives", "")
    
    print("\n[Step 3] Code Generation Agent building the script...")
    llm = get_llm()
    
    prompt_text = "You are the Build Agent. Write the Python code to execute the plan. Return ONLY python code.\n\n"
    if prior_feedback:
        prompt_text += f"CRITICAL: Your previous code failed the Peer Review Swarm. You MUST fix these issues:\n{prior_feedback}\n\n"
    if human_directives:
        prompt_text += f"HUMAN DIRECTIVES (Overrides all other feedback):\n{human_directives}\n\n"
        
    sys_prompt = SystemMessage(content=prompt_text)
    user_prompt = HumanMessage(content=f"Plan: {plan}")
    response = llm.invoke([sys_prompt, user_prompt])
    
    # We will simulate execution by just capturing the code for now
    code_output = _extract_text(response.content)
    return {"code_execution_result": code_output, "messages": [response]}

def step4_peer_review(state: ThinkTankState) -> dict:
    code = state.get("code_execution_result", "")
    plan = state.get("execution_plan", "")
    print("\n[Step 4] Peer Review Swarm analyzing the output...")
    
    llm_flash = get_llm()
    context = f"EXECUTION PLAN:\n{plan}\n\nGENERATED CODE:\n{code}"
    
    # Simulate 3 parallel reviews (sequentially for simplicity in code)
    print("  -> Code Auditor reviewing...")
    r1 = llm_flash.invoke("You are the Code Auditor. Review this python code for bugs: " + context)
    
    print("  -> Math Auditor reviewing...")
    r2 = llm_flash.invoke("You are the Math Auditor. Check the statistical logic here: " + context)
    
    print("  -> Fluke/Bias Checker reviewing...")
    r3 = llm_flash.invoke("You are the Falsifier. Check for look-ahead traps, placebo failures, and confounding variables (e.g. would this signal disappear if controlled for sector/market cap?): " + context)
    
    combined_feedback = f"--- CODE AUDITOR ---\n{_extract_text(r1.content)}\n\n--- MATH AUDITOR ---\n{_extract_text(r2.content)}\n\n--- FALSIFIER ---\n{_extract_text(r3.content)}"
    
    return {"peer_review_feedback": combined_feedback}

def step4_5_final_judge(state: ThinkTankState) -> dict:
    feedback = state.get("peer_review_feedback", "")
    print("\n[Step 4.5] Final Judge structuring the issues...")
    llm = get_llm()
    sys_prompt = SystemMessage(content="You are the Final Judge. Review the Swarm Feedback.\n"
        "1. If there are any critical bugs or falsification traps, the verdict is FAIL. If it is clean, PASS.\n"
        "2. Extract each distinct unresolved issue into a JSON array so a human can review them individually.\n"
        "Format EXACTLY as: {\"verdict\": \"PASS/FAIL\", \"unresolved_issues\": [{\"id\": 1, \"description\": \"Short summary of issue\"}]}\n"
        "Do NOT output markdown blocks, just raw JSON.")
    user_prompt = HumanMessage(content=f"Feedback:\n{feedback}")
    response = llm.invoke([sys_prompt, user_prompt])
    
    try:
        import json
        text = _extract_text(response.content)
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        parsed = json.loads(text.strip())
        return {
            "swarm_verdict": parsed.get("verdict", "FAIL"),
            "unresolved_issues": parsed.get("unresolved_issues", [])
        }
    except Exception as e:
        print(f"Failed to parse Final Judge JSON: {e}")
        return {"swarm_verdict": "FAIL", "unresolved_issues": [{"id": 1, "description": "Failed to parse issues. See raw feedback."}]}

def human_checkpoint_2(state: ThinkTankState) -> dict:
    feedback = state.get("peer_review_feedback", "")
    print("\n" + "="*50)
    print("⏸️ HUMAN CHECKPOINT 2: Final Verdict Decision")
    print("="*50)
    print(f"\n{feedback}\n")
    verdict = input("Enter final verdict (e.g., 'PASS', 'REJECT', 'skip'): ")
    if verdict.strip().lower() == 'skip':
        verdict = "REJECT: Failed placebo test."
    return {"final_verdict": verdict}

def step7_record(state: ThinkTankState) -> dict:
    import datetime
    verdict = state.get("final_verdict", "UNKNOWN")
    task = state.get("task_description", "Unknown Task")
    
    print(f"\n[Step 7] Recording Verdict: {verdict}")
    
    # 1. Save the Single Dynamic Dossier
    dossier_dir = ROOT_DIR / "thinktank" / "dossiers"
    dossier_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    slug = "".join([c if c.isalnum() else "_" for c in task])[:30].lower().strip("_")
    filename = f"{date_str}_{slug}.md"
    filepath = dossier_dir / filename
    
    with open(filepath, "w") as f:
        f.write(f"# Research Dossier: {task}\n\n")
        f.write(f"## Prior Art Report (Step 0b)\n{state.get('prior_art_report', 'N/A')}\n\n")
        f.write(f"## Ideation Explosion (Step 1)\n{state.get('raw_ideas', 'N/A')}\n\n")
        f.write(f"## ⏸️ Human Checkpoint 1 — Approved Ideas\n{state.get('approved_ideas', 'N/A')}\n\n")
        f.write(f"## Execution Plan (Step 2)\n{state.get('execution_plan', 'N/A')}\n\n")
        
        f.write("## Execution History (Step 5 — Self-Correction Loop)\n")
        history = state.get("execution_history", [])
        if history:
            for run in history:
                f.write(f"### Run {run['run']}\n")
                f.write(f"#### Generated Code\n```python\n{run['code']}\n```\n")
                f.write(f"#### Peer Review Feedback\n{run['feedback']}\n")
                f.write(f"#### Verdict: {run['verdict']}\n\n")
        else:
            f.write("No execution history recorded.\n\n")
            
        f.write(f"## Verdict & Registry Entry (Step 7)\nVerdict: **{verdict}**\n")
        
    # 2. Append to task_log.md
    task_log_path = ROOT_DIR / "docs" / "research" / "task_log.md"
    if task_log_path.exists():
        with open(task_log_path, "a") as f:
            f.write(f"\n## {date_str} — {task}  [path: HYPOTHESIS]\n")
            f.write(f"scope: Yes · diverge: AI Agents · converge: Human\n")
            f.write(f"build: Auto · review: Swarm · tests: N/A · verify: N/A\n")
            f.write(f"verdict: {verdict}\n")
            
    return {"dossier_path": str(filepath)}
