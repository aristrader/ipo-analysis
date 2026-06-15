from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from thinktank.orchestration.state import ThinkTankState
from thinktank.orchestration.nodes import (
    step0_triage_history,
    step1_high_ideation,
    step1_5_review_agent,
    human_checkpoint_1,
    step2_execution_planning,
    step3_code_generation,
    step4_peer_review,
    human_checkpoint_2,
    step7_record
)

def build_graph() -> StateGraph:
    """
    Constructs the Think Tank LangGraph pipeline.
    """
    builder = StateGraph(ThinkTankState)

    # 2. Add Nodes
    builder.add_node("Triage", step0_triage_history)
    builder.add_node("Ideation", step1_high_ideation)
    builder.add_node("ReviewAgent", step1_5_review_agent)
    builder.add_node("HumanCheckpoint1", human_checkpoint_1)
    builder.add_node("ExecutionPlan", step2_execution_planning)
    builder.add_node("CodeBuilder", step3_code_generation)
    builder.add_node("PeerReview", step4_peer_review)
    builder.add_node("HumanCheckpoint2", human_checkpoint_2)
    builder.add_node("Record", step7_record)

    # 3. Define the Flow (Edges)
    builder.set_entry_point("Triage")
    builder.add_edge("Triage", "Ideation")
    builder.add_edge("Ideation", "ReviewAgent")
    builder.add_edge("ReviewAgent", "HumanCheckpoint1")
    builder.add_edge("HumanCheckpoint1", "ExecutionPlan")
    builder.add_edge("ExecutionPlan", "CodeBuilder")
    builder.add_edge("CodeBuilder", "PeerReview")
    builder.add_edge("PeerReview", "HumanCheckpoint2")
    builder.add_edge("HumanCheckpoint2", "Record")
    builder.add_edge("Record", END)

    graph = builder.compile()
    return graph

if __name__ == "__main__":
    print("Compiling Full Think Tank LangGraph...")
    graph = build_graph()
    
    print("\nGraph compiled successfully. Structure:")
    try:
        print(graph.get_graph().draw_ascii())
    except Exception as e:
        print(f"(Could not draw graph: {e})")
    
    print("\n--- INITIATING TEST RUN ---")
    initial_state = {
        "task_description": "Hypothesis: Do IPOs with extremely long names underperform because retail investors find them confusing?",
        "messages": [],
        "errors": []
    }
    
    # Run the graph and stream the output
    for s in graph.stream(initial_state):
        # We don't need to print the full state dictionary since nodes.py has print statements
        pass
    
    print("\n--- PIPELINE EXECUTION COMPLETE ---")
