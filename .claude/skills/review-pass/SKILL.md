---
name: review-pass
description: Use this when the build, or a large finished part of it, is ready and the user wants a critical review of the completed code. Spawns review subagents in parallel for backend, frontend, mcp, and data-security. Triggers include "review", "review the code", "code review", "review the build", or invoking /review-pass.
---

# Skill: review-pass

You are running a critical review of finished code on the yipitdata-takehome project. You orchestrate the review agents. You do not review the code yourself and you do not fix anything.

## Protocol

### Step 1 - Determine scope

By default, review everything that is finished. Confirm with the user which parts are done and ready. Do not review work in progress.

### Step 2 - Spawn the review agents in parallel

In a single message, spawn the review agents for the areas that exist, using the Agent tool with `subagent_type` set to each agent name:
- `backend-review` if `backend/` exists
- `frontend-review` if `frontend/` exists
- `mcp-review` if `mcp/` exists
- `data-security-review` always

Each agent runs in its own isolated context and is read-only.

### Step 3 - Consolidate

Merge the agents' findings into one report grouped by severity:
- Blocker
- Should-fix
- Nice-to-have

De-duplicate overlapping findings. Each item keeps its file and line reference and a concrete fix.

### Step 4 - Present, do not fix

Present the consolidated report. Do not auto-fix anything. Fixes happen afterward, in the main thread, decided by the user.

### Step 5 - Offer to update TASKS.md

Offer to add the Blocker and Should-fix items to `TASKS.md`.

## Rules

- The review subagents are read-only and review finished code only.
- Never delegate the fixes to the agents.
- Skip an agent whose area does not exist yet.
- Present findings prioritized, with no hedging.

## When NOT to use

- During active building. Review is for finished code.
- For a single pointed question about one file. Just answer it directly.
