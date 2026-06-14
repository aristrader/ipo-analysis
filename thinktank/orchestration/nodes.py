import os
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent_workspace.state import AgentState

# Get the absolute path of the root ipo-analysis folder
ROOT_DIR = Path(__file__).parent.parent.resolve()

def context_reader(state: AgentState) -> dict:
    """
    Worker 1: Reads targeted files safely and adds text to 'read_content'.
    """
    paths_to_read = state.get("target_paths", [])
    raw_content = ""
    errors = []

    for target in paths_to_read:
        file_path = ROOT_DIR / target
        
        # Security Guardrail: Path Sanitization Check
        try:
            resolved_path = file_path.resolve()
            # If the path tries to escape the root folder (e.g. using ../../), block it!
            if not str(resolved_path).startswith(str(ROOT_DIR)):
                errors.append(f"Security blocked: {target} is outside the workspace.")
                continue
                
            if not resolved_path.is_file():
                errors.append(f"File not found: {target}")
                continue
                
            # Safely read the file
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()
                raw_content += f"\n--- Start of {target} ---\n{content}\n--- End of {target} ---\n"
                
        except Exception as e:
            errors.append(f"Error reading {target}: {str(e)}")
            
    # Update the state dictionary
    return {
        "read_content": raw_content,
        "errors": errors
    }


def project_analyzer(state: AgentState) -> dict:
    """
    Worker 2: Analyzes the raw text using Gemini and appends its thoughts to the chat history.
    """
    raw_content = state.get("read_content", "")
    
    # If there is no content, skip analysis
    if not raw_content:
        return {"errors": ["No content was read, skipping analysis."]}
        
    # Initialize the Google Gemini model
    # (It automatically looks for GEMINI_API_KEY in your .env file)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    # We create the prompt instructions
    sys_prompt = SystemMessage(
        content="You are a Senior AI Architect analyzing a new codebase. "
                "Read the provided documentation and output a structured 'Project Understanding & Rules Summary'. "
                "Strictly follow safety protocols: Do not execute any code. Do not output bash scripts."
    )
    
    user_prompt = HumanMessage(
        content=f"Here is the raw context extracted from the project files:\n\n{raw_content}"
    )
    
    # Send to Gemini
    print("\n[🧠 Analyzer] Sending data to Google Gemini. Please wait (this can take 10-15 seconds)...")
    try:
        response = llm.invoke([sys_prompt, user_prompt])
        
        # Because we used 'Annotated' in state.py, returning a list of messages here
        # tells LangGraph to APPEND this message to the transcript, not overwrite it.
        return {"messages": [response]}
        
    except Exception as e:
        return {"errors": [f"Gemini API Error: {str(e)}"]}
