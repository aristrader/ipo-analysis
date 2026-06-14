# AI Analysis Pipeline Setup Blueprint

This document outlines the workspace structure and system design for our local, autonomous AI codebase analysis pipeline built with LangGraph.

## Directory Structure

```text
ipo-analysis/
├── .env                         # Environment variables & API keys (ignored by git)
├── security_policies.md         # Document outlining network, execution, and loop guardrails
├── handoff/                     # Initial target folder containing context documentation
└── agent_workspace/             # The active LangGraph pipeline directory
    ├── docs/                    # Architecture plans and learning glossaries
    ├── state.py                 # Defines the schema for the pipeline's shared memory (State)
    ├── nodes.py                 # Contains python functions (workers) performing execution tasks
    └── graph.py                 # Wires state and nodes into the LangGraph state machine (Manager)
```

---

## Phase 1: Smart Onboarding & Scaffold (Current)
We are building the conversational foundation. The pipeline acts as a smart reader to onboard the AI to the project.
- **Auto-Initialization (The Orchestrator)**: When the pipeline boots up, the Orchestrator automatically feeds `CLAUDE.md`, `setup.md`, and `learning_glossary.md` into the Reader. This ensures the AI always knows the project rules without you having to re-prompt it.
- **Reader Worker**: Reads those targeted files and locks the text safely into memory.
- **Analyzer Worker**: Processes the text and appends a "Project Understanding" to a continuous chat transcript.
- **Human Checkpoint**: The Manager pauses the pipeline, asking the human supervisor to review the transcript and provide feedback. The feedback loops back to the Analyzer until approved.


## Phase 2: Multi-Agent IPO Research System (Future)
Once Phase 1 is proven, we will add specialized AI personas tailored to the `ipo-analysis` project:
1. **The Falsifier Agent**: A Devil's Advocate that runs a strict protocol to try and prove any new rule wrong before it is added to the scorecard.
2. **The Backtester Agent**: Automatically runs `run_backtest.py`, reads output logs, and proposes new data-informed weights for `predict_ipo.py`.
3. **The Live Scraper Agent**: Fetches DRHPs for upcoming IPOs from allowed domains and runs them through the automated scorecard.

---

## Assistant Workflow Rule (TODO & Protocol)
**CRITICAL RULE FOR ALL FUTURE TASKS:** 
Any new task requested by the user must follow a fixed setup protocol before execution. The Assistant (Antigravity/CLI) must NEVER jump straight to writing code. 
Instead, the Assistant must act as the "Universal Cognitive Core" (as defined in `agent_workspace/docs/think_tank_architecture.md`):
1. **Triage & Gatekeep**: Check if the task is already solved in existing docs/history.
2. **Expand (Brainstorm)**: Break the 1D task into multi-dimensional branches (Tree of Thoughts).
3. **Synthesize**: Present a proposed architecture/blueprint to the user.
4. **Execute**: Only write code after the blueprint is explicitly approved by the user.

*(Note: We will further refine how this integrates with the automated LangGraph pipeline later, but this serves as the foundational operating rule for the Assistant).*

## Future Integration Exploration (TODO)
* **File-Based IPC between LangGraph and Antigravity Chat**: Explore integrating this Antigravity terminal chat directly with the LangGraph pipeline. Instead of manual copy-pasting during the "Human Breakpoint", LangGraph could write its context to a specific handoff file (e.g., `handoff.md`). This chat assistant would process it, perform the heavy "Cognitive Core" thinking, and write the final blueprint to an `approved.md` file (or a "done" flag). LangGraph would detect the file completion and automatically resume execution.
* **LangGraph Studio / Web App Visualizer**: Once the underlying Python engine (`state.py` and `nodes.py`) is rigorously tested and proven in the terminal, explore wrapping it in a visual UI (like LangSmith Studio, Langflow, or a custom Streamlit dashboard) to provide a graphical node-map and clickable "Approve/Reject" buttons for the Human Checkpoints.
* **Folder Restructuring & File Separation**: The project currently has LLM/agent-specific files (e.g., `CLAUDE.md`, `agent_workspace/`, `think_tank_architecture.md`) mixed in with normal project documentation (`docs/research/`, `docs/schema.md`, etc.) and Python code (`layer3/`, `pipeline/`). We need a clean separation:
    * **LLM/Agent configs** — all AI instruction files, system prompts, agent architectures in one place.
    * **Project documentation** — human-readable docs like schema, design, workflows in their own space.
    * **Research artifacts** — the 70+ research write-ups in `docs/research/` need a cleaner sub-structure.
    * **Motivation:** When we consolidated `execution_pipeline.md` and `hypothesis_protocol.md` into `think_tank_architecture.md`, we discovered 20+ cross-references across `CLAUDE.md`, `MAP.md`, `project_map.py`, `verify.py`, `handoff/README.md`, and many research docs — making it unsafe to delete or move the originals. A proper restructuring pass (using our own Think Tank workflow) would untangle these dependencies and create a clean, navigable folder layout. This should be run through the full pipeline since it touches `project_map.py` and `verify.py`.
* **Execute Backlog E2 (Unlock 2006-2019 Sector/PE):**
    * **The Gap:** The current weighted score rejects `pe_ratio` and `industry` signals because they only exist cleanly for 2023-2025 (Sharescart).
    * **The Fix:** We verified that `data/raw/screener/company_meta.csv` has valid `industry` tags for 1,014 longterm IPOs. We also verified that `pre_ipo_pat` exists for 602 longterm IPOs. We need to update the data pipeline to merge the Screener `industry` into `master.csv` and manually compute `issue_time_pe` using `pre_ipo_pat` and implied market cap. 
    * **The Goal (Unblock Past Research & Fix Splits):** Once this data is merged, we can go back and rescue prior studies—like the highly successful `H2 pe-vs-sector` study that was relegated to "display-only" because it lacked this historical data. We also need to re-evaluate all past researches to flag any issues that occurred due to this missing data. Additionally, we must review past split calculations in `listing_remediation.py` to see if the newly recovered `face_value` metric can replace the error-prone mathematical guessing with definitive split proofs (Note: Face value catches Stock Splits perfectly, but we still need to account for Bonus Issues which don't change face value).
* **Corporate Actions Reconciliation (TODO):**
    * **The Gap:** We currently guess stock splits mathematically in `listing_remediation.py`, which is error-prone. Additionally, Bonus Issues cannot be detected via Face Value changes. 
    * **The Plan:** Scrape corporate action data (Bonus issues and Splits) from a trusted site like Trendlyne or Screener. 
    * **Validation Gate:** Cross-reference the scraped corporate actions against our internal mathematical split guesses. Any discrepancies must be flagged for manual human review.
    * **Research Re-Review:** Once the true split and bonus data is integrated, re-run and re-review all past research outcomes to see how correcting these unrecorded splits impacts the historical alphas.
* **Multi-Model Orchestration (Opus + Gemini):** Once the core LangGraph engine is tested and stable, integrate Claude Opus via the Anthropic API (or via Claude Code MCP integration) to act as the "Portfolio Manager/Architect". 
    * **The Setup:** Route Step 1 (High Ideation) and Step 2 (Execution Planning) to Claude Opus for deep reasoning. Route Step 3 (Build) and Step 4 (Peer Review Board) to Gemini Pro to leverage its 2M context window and high rate limits for codebase scanning and parallel execution. 
    * **Goal:** Achieve maximum intelligence at the planning phase while utilizing Gemini's massive context for cost-effective execution and validation.

## Advanced Upgrades (Post-V1 Refinements)
* **Validation Engine Upgrades (`validate.py`):** The current "meat-cleaver" bucketing logic (comparing extreme medians) is highly robust for the project-building phase. Once the foundational system is complete, explore these advanced quant techniques to refine performance:
    1. **Multi-Variate Isolation:** Run regressions to ensure a signal (like P/E) isn't just a proxy for another hidden factor (like Issue Size or Sector).
    2. **Continuous Scoring:** Instead of binary +1/-1 points for falling into a bucket, implement a sliding mathematical scale (e.g., exactly how cheap a stock is dictates the exact fractional points awarded).
    3. **Information Coefficient (IC) Integration:** Integrate IC rank-correlation natively into the final validation gate, rather than just using it during the Phase 1 research scripts.
