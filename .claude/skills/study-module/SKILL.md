---
name: study-module
description: Use this AFTER the build to generate study modules that prepare for the 60-minute live coding session. Each module becomes a learning text plus a self-contained ChatGPT prompt. Triggers include "study module", "generate a study module", "live prep", "study for the interview", or invoking /study-module.
---

# Skill: study-module

You generate study modules so the developer can internalize the code and defend it in the live coding session. Each module is two files: a learning text and a self-contained ChatGPT prompt that acts as teacher then interviewer.

## Protocol

### Step 1 - Read the real code

Read `CLAUDE.md`, `PLAN.md`, the final `README.md`, and the actual code for the module's area. Module content must reflect the real code, not generic theory.

### Step 2 - Decide the modules

Suggest a module list and confirm it with the user. Suggested set:
1. Narrative and architecture (the overview, "tell me about the project")
2. Data model and the QTD / as-of concept
3. Backend: FastAPI and the service layer
4. MCP: server and tool design
5. Frontend: structure and UX decisions
6. Observability, reliability, and scalability
7. Trade-offs and likely follow-up features

### Step 3 - Generate the two files per module

Create `study/` if it does not exist. For each module write:
- `study/NN-<slug>-learning.md` - the learning text, with real code excerpts and the reason behind each decision.
- `study/NN-<slug>-chatgpt-prompt.md` - a self-contained prompt to paste into ChatGPT. The prompt makes ChatGPT teach first, then interview. It includes: an answer key, two explicit phases (teaching then interview), a rigid honest feedback format with no flattery (verdict, then the error, then the correct concept, then ask again), an exit condition, and a short review of the previous module.

### Step 4 - Generate in order

Generate one module at a time, so the user can calibrate the next one from a debrief.

### Step 5 - Record progress

Note the generated modules in `STATE.md` and `TASKS.md`.

## Rules

- Content reflects the real code in this repo, with concrete file paths.
- Each module stands alone and is studied by active recall, not passive reading.
- The focus is defending decisions live, not trivia.
- No em-dash or en-dash.

## When NOT to use

- Before the build is finished. There is no real code to study yet.
