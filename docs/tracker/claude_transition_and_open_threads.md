# Claude Transition & Open Work Streams

This document serves as the master "save state" for the project. We have successfully completed the massive documentation cleanup and repository restructuring. However, several critical architectural threads were paused to prepare for the switch to Claude. 

**Pick up this document tomorrow when you boot up Claude Code.**

---

## Part 1: Claude Code Token Optimization Guide
*To avoid burning through your $20 budget in a single session, implement these strategies immediately upon starting Claude Code:*

1. **The "Caveman" Plugin (Output Minification)**
   - **Installation:** Run `claude plugin marketplace add JuliusBrussee/caveman` then `claude plugin install caveman@caveman`.
   - **Usage:** Type `/caveman` to force Claude to drop conversational filler. Saves 65-75% on output tokens.
2. **Context Rot & The `/compact` Command**
   - Claude resends the *entire terminal history* with every prompt. 
   - Type `/compact` every 20-30 minutes to summarize history and drop raw logs.
   - Type `/clear` when you completely switch to a new task to wipe the slate clean.
3. **Filter Terminal Commands**
   - Do not let Claude run raw commands like `npm test` or `git status` blindly, as the full output bloats the context.
   - Rule (already in `CLAUDE.md`): Claude must pipe shell outputs (e.g., `... | grep -A 5 "FAIL"`).
4. **The "Antigravity Hook" (Meta-Orchestration)**
   - When Claude needs to read the 70+ markdown files in `docs/research/`, it should **not** read them directly.
   - Claude should run a terminal command to trigger Gemini (Antigravity CLI) to read the files and return a minified 200-word summary. 

---

## Part 2: Active & Open Work Streams (Where we left off)

We were bouncing between several major architectural decisions. Here is the exact state of what is open and needs to be finalized:

### 1. Finalizing the Meta-Orchestration Architecture
- **The Core Question:** Who is orchestrating what? 
- **The Pivot:** Originally, we were trying to build a "manual copy-paste handoff" inside `thinktank/orchestration/ui.py` to pause the LangGraph so you could use the Claude Web UI. We pivoted to the idea of using the **Claude Code CLI** as the master orchestrator, using Gemini as a backend tool.
- **Open Action:** You need to explicitly decide the final architecture. Does Claude Code replace `graph.py`? Or does Claude Code *write* a python wrapper that dynamically calls the Claude API for reasoning and the Gemini API for context? Where do the API keys go?

### 2. Think Tank UI & Human Feedback Loop
- **The Current State:** `ui.py` is currently running a tight, synchronous `for i in range(2):` loop that completely bypasses the nice node/edge structure defined in `graph.py`. 
- **Open Action:** We need to rebuild the human-in-the-loop feedback mechanism in the Streamlit app so that you can effectively pause the autonomous research agents, provide directives, and resume them cleanly. 

### 3. Think Tank Internal Improvements
- **The Current State:** We merged all technical debt into `docs/tracker/improvement_backlog.md`. We successfully updated `ui.py` to save deferred hypotheses correctly to the new `docs/research/backlog/` structure.
- **Open Action:** The execution pipeline's logic (running hypotheses against the data) is technically functional but needs to be rigorously tested once the dual-model orchestration is wired up. 

### Next Steps for Tomorrow:
1. Boot up Claude Code CLI.
2. Give Claude this file: `Read docs/tracker/claude_transition_and_open_threads.md to understand where we left off.`
3. Start with **Item 1** (Finalizing the Orchestration Architecture).
