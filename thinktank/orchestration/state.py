from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import AnyMessage

class ThinkTankState(TypedDict):
    """
    The Shared State for the Think Tank Research Lab LangGraph pipeline.
    """
    # 1. Inputs
    task_description: str
    dossier_path: str
    
    # 2. Step 0: Triage & History
    prior_art_report: str
    
    # 3. Step 1: Ideation
    raw_ideas: str
    
    # 4. Step 1.5: Review Agent (Keep/Cut/Open)
    sorted_ideas: str
    
    # 5. Checkpoint 1: Human Approval
    approved_ideas: str
    
    # 6. Step 2: Execution Plan
    execution_plan: str
    
    # 7. Step 3: Build & Execute
    code_execution_result: str
    
    # 8. Step 4: Peer Review
    peer_review_feedback: str
    
    # 8.5 Step 4.5: Final Judge
    swarm_verdict: str
    unresolved_issues: List[dict]
    
    # 9. Step 5: Self-Correction Loop
    execution_history: List[dict]
    prior_swarm_feedback: str
    human_directives: str
    human_retry_count: int
    
    # 10. Step 7: Record
    final_verdict: str
    
    # Chat Transcript for LLM interactions
    messages: Annotated[List[AnyMessage], operator.add]
    
    # Error Logging
    errors: List[str]
