# Reusable LangGraph Architecture Template

Use this blueprint to quickly set up a safe, conversational AI pipeline in any future Python project.

## 1. Required Libraries
```bash
pip install langgraph langchain langchain-google-genai python-dotenv
```

## 2. Standard Directory Structure
```text
project_root/
├── .env                         # API Keys (e.g., GEMINI_API_KEY)
├── security_policies.md         # Design rules for path safety and loop prevention
└── agent_workspace/
    ├── docs/                    # Architecture plans and glossaries
    ├── state.py                 # Defines `AgentState` schema (Input, Raw Data, Messages, Errors)
    ├── nodes.py                 # Python worker functions (e.g., Reader, Analyzer)
    └── graph.py                 # Wires nodes into a StateGraph with a human-in-the-loop interrupt
```

## 3. The Core Architectural Philosophy
**Always separate Raw Facts from AI Opinions.**
1. **The Reader Worker** securely targets local files and locks the text into `read_content`. It does no thinking.
2. **The Analyzer Worker** reads `read_content` and appends its reasoning to a continuous `messages` chat transcript.
3. **The Manager (Graph)** pauses the pipeline to ask the human for feedback.
4. The human provides feedback, which is appended to `messages`, and the loop repeats (back-and-forth conversation) until the human approves the outcome.
