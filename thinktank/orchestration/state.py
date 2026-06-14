from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    """
    The Shared Notepad for the IPO Analysis pipeline.
    Uses 'Annotated' to append messages like a chat transcript instead of overwriting them.
    """
    # 1. Input: Files to read (e.g., ["CLAUDE.md", "MAP.md"])
    target_paths: List[str]
    
    # 2. Raw Data: The untouched text extracted from target_paths
    read_content: str
    
    # 3. Chat Transcript: A continuous history of AI summaries and human feedback
    # 'operator.add' ensures that new messages are appended to the list, not overwritten.
    messages: Annotated[List[AnyMessage], operator.add]
    
    # 4. Error Logging: A place to write errors (e.g., "File not found")
    errors: List[str]
