# AI Pipeline Security and Guardrail Policies

This document outlines the security architecture and defensive guardrails established for our codebase analysis pipeline. These rules govern both the developer environment (Antigravity) and the Python code we are building.

---

## 1. Environment-Level Security (Antigravity Sandbox)

We rely on the existing configurations in [`.claude/settings.local.json`](file:///Users/swapnilagarwal/Visual_Studio_Projects/ipo-analysis/.claude/settings.local.json) to secure the agent's environment:

- **Network Whitelisting (Default-Deny)**: The agent can only fetch data from specific financial domains (e.g., `sebi.gov.in`, `bseindia.com`, `nseindia.com`, `screener.in`). Any attempt to fetch from a new domain requires manual user approval.
- **Blocked Operations**: Unsafe code execution via the browser (`mcp__playwright__browser_run_code_unsafe`), direct browser network requests, and external file uploads are strictly denied.
- **Git Remote (branch + PR)**: The repo has a GitHub remote (`origin` → `github.com/aristrader/ipo-analysis`). Work happens on branches that are pushed + opened as PRs; direct pushes to `main` require explicit owner approval. No secrets/keys/tokens are ever committed.

---

## 2. Pipeline-Level Security (Our LangGraph Code)

To ensure our custom pipeline behaves safely and cannot be compromised (e.g., via malicious files in the `handoff/` folder or prompt injection), we enforce the following guardrails in our code:

### A. Path Sanitization & Boundary Protection
The file-reading node (`context_reader`) must block any attempts to access files outside the `handoff/` directory.
- **Implementation**: The node will resolve absolute paths and raise a security exception if any path traverses outside the `handoff/` directory (e.g., using `..` to read `.env` or SSH keys).

### B. Network Request Allowlist
If the pipeline needs to scrape or fetch data from the web in later phases:
- We will construct a helper `SafeHttpClient` class.
- This class will match target URLs against a hardcoded domain whitelist and reject any request that does not match.

### C. Static Analysis Only (No Arbitrary Execution)
The pipeline reviews code strictly as static text.
- **Constraint**: The Python nodes will never use `eval()`, `exec()`, or execute code via `subprocess` or `os.system()`. 
- The AI's job is to *read* and *explain*, not to *run* the code.

### D. Prompt Injection Protections
When asking the LLM to analyze code, system prompts will carry safety envelopes:
- Instructions will instruct the model to report code issues, but never output executable bash scripts or instruct the pipeline to run commands.

### E. Loop and Rate-Limit Guardrails
To prevent infinite loop conditions in LangGraph that would hang your local terminal or exhaust your API rate limits:
- **Max Steps limit**: The graph configuration will enforce a strict limit on the number of active node transitions (e.g., maximum 10 steps). This ensures the program terminates safely if it gets stuck in a cycle.


### F. Human-in-the-Loop Breakpoints
No destructive, external, or writing actions can occur automatically. The graph uses LangGraph’s state interruption feature to halt the execution and request a manual command-line confirmation before moving past the analysis stage.
