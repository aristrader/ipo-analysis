# AI & LangGraph Glossary

Keep this file handy as a quick reference for all the AI engineering jargon we use.

- **LangGraph**: A library to build AI workflows as a "State Machine" (think of it as a relay race where workers pass around a shared notepad).
- **State (`TypedDict`)**: The exact shape of the "Shared Notepad" in the computer's memory that holds all the data being passed between workers.
- **Node**: A single worker or step in the pipeline (e.g., a simple Python function that reads a file, or a function that calls Gemini).
- **Human-in-the-loop (Breakpoint)**: Pausing the automated workflow to ask a human supervisor for approval, feedback, or instructions before it can finish.
- **Message Appending (`Annotated[List, add]`)**: A technique to keep a continuous chat history transcript, allowing a "to-and-fro" conversation instead of overwriting the AI's previous thoughts.
- **GraphRAG / Vector Database**: A complex search engine system for mapping massive, messy codebases (which we don't need, because our project is already perfectly mapped via `MAP.md`).
- **Multi-Agent Workflow**: An advanced system where multiple specialized AI personas (e.g., a Reader Agent, a Backtester Agent, a Falsifier Agent) work together like a corporate team to solve complex problems.
- **Hallucination**: When an AI model gets confused and confidently makes up a fake fact or writes incorrect code. (This is why we architect our pipeline to never overwrite the raw source data with AI opinions).
