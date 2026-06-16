# The Foundry — App Development Cognitive Architecture v2

> **This is the ONE file.** It defines the autonomous Think Tank architecture specifically
> tailored for Software Engineering, Web Development, and UI/UX Design.
> It runs parallel to the Quantitative Research Think Tank (`think_tank_architecture.md`).
>
> Everything an agent needs to build, review, and ship a feature lives here. No cross-referencing required.

---

## Philosophy

> "Aesthetics are very important. If your web app looks simple and basic then you have FAILED!" — System Mandate

> "Speed of execution is not that important; what is more important is the accuracy and correctness." — Owner mandate

The system is an **autonomous software engineering foundry**, not a code factory. Every application or component must survive:
- Deep multi-dimensional UX ideation (not just MVP — "WOW" factor designs with multiple competing approaches)
- Human architecture & design approval
- Codebase-grounded execution planning
- Specialized peer review (Architecture, UX/Aesthetics, Security/Performance — separate agents)
- Automated test coverage verification
- Fix-to-stop-rule loop (no infinite grinding)

No feature ships to the user without surviving all of these gates.

---

## TRIAGE FIRST — Which Path?

Top-down, FIRST match wins. Never self-rationalize into a lighter path.

| Path | When | What's required |
|---|---|---|
| **FULL STACK** | New web app, complex dashboard, database-backed feature, or any user-facing surface | Full architectural review, all 3 swarm reviewers, and automated test suite. All steps below. |
| **UI/UX COMPONENT** | Adding a specific visual element, interaction, or page | Heavy emphasis on the Aesthetics Auditor. At minimum: Diverge (2 lenses) + Build + UX Review + Test. |
| **BACKEND ROUTE** | API endpoints, data pipelines, server logic | Heavy emphasis on the Security/Performance Auditor. At minimum: Diverge (1 red-team lens) + Build + Security Review + Test. |
| **HOTFIX** | Urgent bug fix | Say "hotfix" out loud. MINIMAL safe change + test. LOG it. Backfill review next turn. The only sanctioned skip. |
| **TRIVIAL** | True one-liner / typo / CSS tweak | Just do it. No ceremony, no log. |

"Non-trivial" = more than a one-liner OR touches a user-facing surface, state management, routing, or API layer. When unsure, go one tier heavier, not lighter.

---

## THE PIPELINE — All Steps

### Step 0: Scope & Context

Confirm the requirements exist and are clear BEFORE designing. State the task + success criteria in one line.

1. **What is being built?** (New app / New page / New component / Bug fix)
2. **Who is the user?** (The owner / External users / Other agents)
3. **What is the tech stack?** (Streamlit / Vanilla HTML+JS+CSS / Next.js / Vite — confirm before touching code)
4. **What data does it consume?** (API endpoints / CSV files / LangGraph state / None)

### Step 0b: History Check — Has This Been Built Before?

Before any ideation, the agent MUST:
1. **Read `project_map.py`** — the master registry of all files, their purposes, and their locations. If a similar component already exists, REUSE or EXTEND it. Do not build a duplicate.
2. **Read `docs/setup.md`** — the living backlog of future integration tasks. Check if this task is already tracked.
3. **Read `docs/tracker/task_log.md`** — check if a prior session already attempted this.
4. **Scan the existing `app/` directory** — understand what pages, components, and styles already exist. New code must integrate cleanly with existing patterns.

**Output:** A brief "Prior Art Report" confirming whether this feature is novel or extends an existing component. If prior art exists, state it and ask the human whether to reuse or rebuild.

---

### Step 1: High Ideation — The UX Brainstorm (DIVERGE)

**The Goal:** Transform a single feature request into 5-10 distinct implementation approaches ranging from minimal utility to cutting-edge "WOW" experiences. Not 2 vague bullet points — structured, concrete proposals with wireframe-level detail.

**The Model:** High-intelligence reasoning model. This is the most expensive step and the most valuable. Do not use a cheap model here.

**Diverge mechanics:** 3 DISTINCT lenses, spawned in PARALLEL, wait for all. Each agent returns a FIXED contract:
```
PROPOSALS (each: what · wireframe description · technical stack · effort S/M/L · aesthetic-tier basic/premium/luxury)
TOP PICK
BLOCKERS/TRAPS (e.g., "Streamlit can't do custom CSS animations natively")
```
Essays don't converge — enforce the contract.

**The 3 Lenses:**

1. **The Minimalist/Functional Lens:**
   - Clean, utilitarian, fast to build.
   - Focus: Does it work? Is it accessible? Is it fast?
   - Trade-off: May look generic.

2. **The Premium/Dynamic Lens:**
   - Glassmorphism, smooth micro-animations, tailored HSL color palettes.
   - Modern typography (Google Fonts: Inter, Roboto, Outfit — never browser defaults).
   - Subtle gradients, hover effects, dynamic transitions.
   - Dark mode or themed color schemes.
   - Trade-off: Higher effort, more CSS complexity.

3. **The Architecture/Red-Team Lens:**
   - Server-side vs. Client-side rendering trade-offs.
   - Framework choice (Vanilla vs Next.js/Vite — only if user explicitly requested).
   - State management strategy (session_state / React hooks / Vanilla JS closures).
   - Scalability: Will this design break when data grows 10x?
   - **Red-team:** What could go wrong? What edge cases will crash this? What looks good on desktop but breaks on mobile?

**Example — The Dashboard Feature Chain of Thought:**
- *Seed:* "Build a dashboard to visualize IPO performance."
- *Chain of Thought Explosion:*
    1. Should it be a Streamlit app (quick) or a full HTML/JS app (premium)?
    2. What charts are needed? (Bar, Line, Scatter, Heatmap, Treemap)
    3. Should charts be interactive (hover tooltips, zoom, click-to-filter)?
    4. Should there be a filter sidebar (date range, IPO type, sector)?
    5. Should it support dark mode?
    6. Should it lazy-load data for performance?
    7. Should there be a comparison mode (compare 2 IPOs side-by-side)?
    8. What about mobile responsiveness?
    9. Should there be an export button (CSV, PDF)?
    10. Should the layout use a grid system or a single-column flow?

**Documentation Output:** Findings appended to the **Single Dynamic Dossier** (see §UX Strategy below).

---

### Step 1.5: The Architecture Review Agent (CONVERGE)

Before the human sees the massive brainstorm, an automated Review Agent executes an explicit **keep/cut test** on the raw proposals:

- **Rule:** Keep an item ONLY if ALL THREE conditions are met:
    1. **(High user value)** — Does the owner actually need this, or is it feature creep?
    2. **(Technically feasible in our stack)** — Can we build it with our current tools (Streamlit, Vanilla JS, Python)?
    3. **(Meets the premium aesthetic bar)** — Would the owner say "WOW" when they see this?

- **Output:** The agent outputs a pre-sorted `IN / CUT / OPEN` specification list. It must briefly justify why generic or infeasible ideas were moved to CUT.

---

### ⏸️ HUMAN CHECKPOINT 1: Design & Architecture Approval

The human reviews the Review Agent's pre-sorted `IN / CUT / OPEN` list. The human acts as the Product Manager:
- **Review:** The human reads the sorted list, saving them the effort of reading 10 raw proposals.
- **Move:** The human can promote a CUT idea to IN, or move an IN idea to CUT if they disagree with the Review Agent.
- **Expansion:** The human can manually add new requirements, specify preferred colors, or inject their own UX preferences.
- **Selection:** The human selects the final specific UX flow and technical architecture to push forward to execution.

---

### Step 2: Execution Planning — The Codebase-Grounded Blueprint (PLAN)

**The Goal:** For each approved design, define *exactly* how the app will be built — before writing a single line of code.

Break into small, independently-testable sub-tasks. Builds are SEQUENTIAL (parallel edits to the same files conflict).

**Mandatory Codebase Grounding (the agent must read these files):**

| File | What it teaches the planner |
|---|---|
| `project_map.py` | The master file registry. Know where everything lives. Know what already exists. |
| `app/` directory | Existing app pages, components, and styles. New code MUST integrate cleanly. |
| `requirements.txt` | Current Python dependencies. Do NOT add new pip packages without documenting WHY. |
| `docs/schema.md` | If the feature reads data, confirm the required columns exist. |
| `.streamlit/config.toml` | If Streamlit, understand the current theme and server config. |

**The Blueprint Must Define:**

1. **Foundation (CSS/Styling):**
   - Color palette (exact hex/HSL values, not "blue" or "red").
   - Typography (font family, weights, sizes).
   - Spacing system (consistent padding/margin scale).
   - Animation definitions (transition durations, easing curves).

2. **State Management:**
   - What data flows through the app?
   - How is user interaction state stored? (Streamlit `session_state` / React hooks / Vanilla JS objects)
   - What happens on page refresh? Is state lost?

3. **Component Decomposition:**
   - Exact files to be created, with one-line descriptions.
   - Component hierarchy (parent → child relationships).
   - Data flow diagram (which component reads what, passes what to whom).

4. **SEO & Accessibility (non-negotiable):**
   - Proper `<title>` tags for each page.
   - Compelling `<meta>` descriptions.
   - Single `<h1>` per page with proper heading hierarchy (`h1` → `h2` → `h3`).
   - Semantic HTML5 elements (`<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`).
   - Unique, descriptive `id` attributes on all interactive elements.
   - `aria-label` on non-obvious interactive elements.
   - Keyboard navigation support (tab order, focus indicators).

5. **Test Plan:**
   - What test cases will be written?
   - What user flows will be validated?
   - What edge cases are expected?

**Documentation Output:** Execution plan appended to the Single Dynamic Dossier.

---

### Step 3: Code Generation & Testing (BUILD — TDD)

- **TDD:** Failing test → minimal code → green → commit. Small steps, frequent commits.
- **Environment:**
  - `PYTHONPATH=. .venv/bin/python` (plain `python` doesn't exist on this box).
  - Streamlit apps: `PYTHONPATH=. .venv/bin/streamlit run <file> --server.headless true`
  - New packages: Install into `.venv` via `.venv/bin/pip install <package>`. Update `requirements.txt`.
  - **GIT: branch + PR, push freely** to `origin` (github.com/aristrader/ipo-analysis); NEVER push directly to `main` without owner approval. Company laptop: Streamlit localhost-only, no secrets/keys/tokens in commits.

- **Aesthetics Mandate (non-negotiable):**
  - **Colors:** Never use generic red, blue, green. Use curated, harmonious color palettes with HSL-tailored values.
  - **Typography:** Always use modern fonts from Google Fonts (Inter, Roboto, Outfit). Never use browser defaults.
  - **Gradients:** Use smooth gradients over flat colors.
  - **Micro-animations:** Every interactive element must have hover effects, smooth transitions, or subtle motion. An interface that feels responsive and alive encourages interaction.
  - **Spacing:** Consistent, generous whitespace. Cramped layouts feel cheap.
  - **Dark mode:** Prefer dark mode designs unless the user explicitly requests light mode.
  - **No placeholders:** If an image is needed, use the internal `generate_image` tool to create a working demonstration asset. Never ship a broken image icon.

- **Framework Rules:**
  - Default: HTML + JavaScript + Vanilla CSS for maximum flexibility and control.
  - Streamlit: Use for rapid internal tools and data dashboards.
  - Next.js / Vite: ONLY if the user explicitly requests a web app framework. Use `npx -y` with `--help` first, initialize with `./`, run in non-interactive mode.
  - TailwindCSS: ONLY if the user explicitly requests it. Confirm version first.

- **Test Coverage Requirements:**
  - Every new component must have at least one test case.
  - Use Streamlit's `AppTest` framework for Streamlit apps.
  - Use `pytest` for backend logic.
  - Test user interaction flows: input changes, button clicks, state transitions.
  - Test edge cases: empty data, very long strings, special characters.
  - Test responsiveness: Does the layout break at different viewport widths?

---

### Step 4: The Peer Review Board (REVIEW — The Specialized Swarm)

The post-build review repeatedly catches what pre-build divergence cannot. The owner does NOT read code, so the review swarm IS the quality gate.

Before the human sees the app, a swarm of specialized reviewers examines the codebase:

**Reviewer 1 — The Architecture Auditor:**
- Is the component logic modular and reusable?
- Is state mutated safely? Are there race conditions?
- Are imports and dependencies correct? Were any new packages added without documentation?
- Does the code follow the agreed-upon execution plan from Step 2?
- Is there dead code or unused imports?
- Are file paths correct (absolute vs relative)?
- Does the new code integrate cleanly with existing `app/` components?
- Run the test suite: `PYTHONPATH=. .venv/bin/pytest tests -q` must be green.

**Reviewer 2 — The UX & Aesthetics Auditor (The "WOW" Checker):**
- **CRITICAL GATE:** Does this look basic, or does it look premium? If it looks like a generic MVP, this auditor MUST reject the build.
- **Color Check:** Are the colors harmonious? Are they using curated HSL palettes, not generic CSS named colors?
- **Typography Check:** Is the font modern (Inter, Outfit, Roboto)? Is the hierarchy clear (size, weight, spacing)?
- **Animation Check:** Do interactive elements have hover effects? Are transitions smooth (200-300ms, ease-out)?
- **Spacing Check:** Is whitespace consistent? Does the layout breathe, or is it cramped?
- **Responsive Check:** Does the layout work on mobile (320px), tablet (768px), and desktop (1440px+)?
- **Consistency Check:** Do all buttons/inputs/cards follow the same visual pattern?
- *Example PASS:* "The dashboard uses a dark theme with HSL(220, 15%, 12%) background, Inter font at 14px/16px/24px hierarchy, smooth 250ms fade-in animations on cards, and consistent 16px/24px spacing grid."
- *Example REJECT:* "The form uses browser-default inputs with no styling, the background is plain white, and there are no hover effects on any buttons."

**Reviewer 3 — The Security & Performance Auditor:**
- **XSS Check:** Is user input sanitized before rendering? Are `innerHTML` or `dangerouslySetInnerHTML` used safely?
- **Injection Check:** Are database queries parameterized? Are file paths validated?
- **Secrets Check:** Are API keys, tokens, or passwords hardcoded? They MUST come from `.env` only.
- **Performance Check:** Are there unnecessary re-renders? Is data loaded lazily where appropriate?
- **Memory Check:** Are event listeners cleaned up? Are intervals/timeouts cleared on unmount?
- **Accessibility Check:** Do all interactive elements have unique IDs? Are `aria-label` attributes present?
- **Network Check:** Streamlit localhost-only, no external API calls without explicit approval. No secrets in git.

**The Disagreement Rule:** If Reviewer 2 (Aesthetics) flags the app as "basic" or "generic," the build is REJECTED and sent back to Step 3 for redesign. Aesthetics are non-negotiable. If reviewers conflict on architecture vs performance, surface the trade-off to the owner.

---

### ⏸️ HUMAN CHECKPOINT 2: Interactive Review

The pipeline pauses. The human reviews the Single Dynamic Dossier containing:
1. What was designed (from Step 1 + Step 2)
2. The built application (from Step 3) — the human can test the live app
3. The Peer Review Board's verdicts with reasoning (from Step 4)
4. For each aspect: PASS (with evidence) / REJECT (with specific fix instructions)

The human can:
- Accept the build and promote it to production
- Reject the build with specific UX feedback (e.g., "make the animation faster", "darken the secondary color")
- Request additional components or features
- Ask "why did this pass/fail?" and get the full reasoning chain

---

### Step 5: Fix → Re-Review Loop

Loop review↔fix until a pass finds ZERO new aesthetic, architectural, or security findings.

**STOP RULE:** If a 3rd pass still finds new issues → STOP and escalate to the owner (don't grind). Something fundamental is wrong with the design.

---

### Step 6: Test + Verify

- `PYTHONPATH=. .venv/bin/pytest tests -q` — all green.
- Streamlit boot test: `PYTHONPATH=. .venv/bin/streamlit run <file> --server.headless true` — starts cleanly, no import errors.
- If HTML/JS: Open in browser, check console for JavaScript errors.
- Verify `project_map.py` is updated if new files were created.

---

### Step 7: Record & Clean Up

1. Append a task entry to `docs/tracker/task_log.md` (see §Checkable Artifacts).
2. Update `docs/setup.md` if this resolves a tracked TODO.
3. Update `project_map.py` if structure changed.
4. Commit with the pipeline trailer: `Pipeline: path=FULL_STACK diverge=3 review=swarm tests=green`.

**DONE = ALL of:** success criteria met · review clean · test suite green · UI boots cleanly · docs updated · committed with trailer · task_log entry closed. Anything open → not done.

---

## UI-TRUTH INVARIANTS

Check at REVIEW + VERIFY — the hard-won rules. Violating one = a bad user experience.

- **No browser defaults:** Every visible element must be explicitly styled. Default fonts, default input borders, default button styles = automatic rejection.
- **No broken assets:** Every image must load. Every icon must render. Every link must resolve. Use `generate_image` for missing assets — never ship placeholder.svg or broken-image icons.
- **No magic numbers:** CSS values must come from a defined design system (spacing scale, color palette, type scale). Random `padding: 13px` or `color: #3a7bc8` without explanation = tech debt.
- **State survives interaction:** Clicking a button, changing a dropdown, or navigating must not lose user state unless explicitly intended. Test this.
- **Responsive or bust:** If it doesn't work at 320px width, it doesn't ship. Test on mobile viewport.
- **Accessible by default:** Keyboard navigation must work. Screen readers must be able to parse the content. Color contrast must meet WCAG AA (4.5:1 for text).

---

## STANDING CONSTRAINTS (always)

Env: `PYTHONPATH=. .venv/bin/python`; Streamlit localhost-only; no secrets/keys/tokens in commits; `.env` for all API keys (load via `python-dotenv`). **GIT: branch + PR, push freely** to `origin` (github.com/aristrader/ipo-analysis); NEVER push directly to `main` without owner approval. No external network requests without explicit owner approval. Playwright OFF by default (`docs/playwright_on_off.md`).

---

## THE CHECKABLE ARTIFACTS

Makes "followed the pipeline" a FACT on disk, not a claim.

**`docs/tracker/task_log.md`** — append-only, ONE entry per non-trivial task. Template:
```
## YYYY-MM-DD — <task one-liner>  [path: FULL_STACK|UI_COMPONENT|BACKEND|HOTFIX]
scope: <requirements confirmed?>  · diverge: <lenses / agent ids>  · converge: <spec / IN-CUT>
build: <commits>  · review: <swarm verdict>  · tests: <suite>  · boot: <clean?>
verdict: <honest outcome>
```

**Commit trailer** on the task's final commit: `Pipeline: path=FULL_STACK diverge=3 review=swarm tests=green`.

---

## UX & Documentation Strategy — The Single Dynamic Dossier

**Problem:** Too many `.md` files confuse the human. Complex folder structures hide information.

**Solution:** For each app development task, the agents maintain ONE file: `thinktank/dossiers/YYYY-MM-DD_<feature_slug>.md`.

As the pipeline progresses, each step APPENDS to this file under clear headers:
```markdown
# Feature Dossier: <Feature Name>
## Prior Art Report (Step 0b)
## UX Brainstorm (Step 1)
## ⏸️ Human Checkpoint 1 — Design Decision
## Execution Blueprint (Step 2)
## Build Log (Step 3)
## Peer Review Swarm (Step 4)
## ⏸️ Human Checkpoint 2 — Interactive Review
## Verdict & Task Log Entry (Step 7)
```

The human only ever needs to open ONE file to see the full journey of a feature from seed to ship.

---

## Model Routing Strategy

| Step | Requirement | Model |
|---|---|---|
| Step 0 (Triage) | Fast classification | `gemini-2.5-flash` |
| Step 0b (History Check) | File reading + matching | `gemini-2.5-flash` |
| Step 1 (High Ideation) | Deep reasoning, UX creativity | `gemini-2.5-pro` or CLI offload (highest quality) |
| Step 2 (Execution Planning) | Codebase reading + architecture | `gemini-2.5-pro` or CLI offload |
| Step 3 (Code Generation) | Code writing + testing | `gemini-2.5-pro` or CLI offload |
| Step 4 (Peer Review Board) | Each reviewer: focused analysis | `gemini-2.5-flash` (parallelizable; 3 independent reviewers) |
| Step 7 (Recording) | Documentation | `gemini-2.5-flash` |

**Rate-limit safety:** On the free tier, parallel `pro` calls may hit 429 errors. Use "CLI Offloading" (pasting complex logic into the Antigravity chat) as a fallback for Step 1 and Step 2.

---

## Future Integration (TODO — tracked in `setup.md`)
- **Visual Design Mockup Generation:** Use `generate_image` during Step 1 to create visual wireframe mockups that the human can review before any code is written.
- **Live Preview Integration:** Auto-launch Streamlit or a local dev server during Human Checkpoint 2 so the human can interact with the build in real-time.
- **Component Library:** Build a shared design system (`app/design_system/`) with reusable styled components, color tokens, and animation presets so every new feature starts from a premium baseline.

---

## KICKOFF (paste at task start)

> A non-trivial app development task is picked. Triage the path, then execute the steps in this document:
> scope-requirements → history-check → diverge (parallel multi-lens agents: minimalist · premium · red-team,
> fixed output contract) → ⏸️ human design approval → plan (codebase-grounded, component-decomposed) →
> build (TDD, aesthetics-mandated) → peer review swarm (architecture + aesthetics + security) →
> ⏸️ human interactive review → fix-to-stop-rule → test+verify+boot → cleanup with task_log entry +
> pipeline commit trailer. Honor the UI-TRUTH INVARIANTS and STANDING CONSTRAINTS.
> If skipping a stage, say which and why up front.
