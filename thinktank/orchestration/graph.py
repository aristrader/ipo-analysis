from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agent_workspace.state import AgentState
from agent_workspace.nodes import context_reader, project_analyzer

def build_graph():
    """
    Builds the LangGraph state machine workflow.
    """
    # 1. Initialize the Graph with our Shared Notepad template
    workflow = StateGraph(AgentState)
    
    # 2. Add our Workers
    workflow.add_node("reader", context_reader)
    workflow.add_node("analyzer", project_analyzer)
    
    # 3. Define the routing (The Relay Race)
    workflow.add_edge(START, "reader")
    workflow.add_edge("reader", "analyzer")
    workflow.add_edge("analyzer", END)
    
    # 4. Add Memory and the Human Breakpoint
    # We compile the graph with a memory saver, and tell it to explicitly PAUSE after the analyzer.
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_after=["analyzer"])
    
    return app

def run_pipeline():
    """
    The Orchestrator script that boots up the pipeline.
    """
    app = build_graph()
    
    # LangGraph requires a 'thread_id' to remember the conversation
    config = {"configurable": {"thread_id": "session_1"}}
    
    # === AUTO-INITIALIZATION ===
    # The pipeline boots up and automatically feeds its own rules to the Reader
    initial_state = {
        "target_paths": [
            "CLAUDE.md",
            "setup.md",
            "agent_workspace/docs/learning_glossary.md"
        ]
    }
    
    print("\n[⚙️ Orchestrator] Starting Auto-Initialization...")
    print("[⚙️ Orchestrator] Waking up the Reader Worker to read project rules...")
    
    # Run the graph until it hits the breakpoint
    for event in app.stream(initial_state, config=config, stream_mode="values"):
        if "errors" in event and event["errors"]:
            print(f"\n[🚨 Error] {event['errors'][-1]}")
            
    print("\n[⏸️ Orchestrator] Pipeline paused at Human Breakpoint.")
    
    # Fetch the state at the breakpoint
    current_state = app.get_state(config)
    messages = current_state.values.get("messages", [])
    
    if messages:
        print("\n" + "="*50)
        print("🤖 AI's Project Understanding:")
        print("="*50)
        print(messages[-1].content)
        print("="*50 + "\n")
        
    print("This is the Human-in-the-Loop Breakpoint.")
    print("Type your feedback to tell the AI what it missed, or type 'approve' to finish.")
    
    try:
        feedback = input("Your Feedback > ")
        if feedback.lower() in ["approve", "approved", "exit", "quit", "yes"]:
            print("\n[✅ Orchestrator] Pipeline Approved and Completed.")
        else:
            print("\n[🔄 Orchestrator] In Phase 2, this feedback will loop back to the Analyzer!")
    except EOFError:
        print("\n[✅ Orchestrator] Pipeline Exited.")

if __name__ == "__main__":
    # If you run this file from the terminal, it will start the pipeline!
    run_pipeline()
