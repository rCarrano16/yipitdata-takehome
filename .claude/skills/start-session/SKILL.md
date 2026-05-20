---
name: start-session
description: Use this at the START of a work session on the yipitdata-takehome project. Rebuilds context by reading CLAUDE.md, STATE.md, TASKS.md, and the assignment brief, then briefs the user. Triggers include "start session", "resume", "continue", "where did we stop", "let us continue", or invoking /start-session.
---

# Skill: start-session

You are resuming work on the yipitdata-takehome project. Your only job in this activation is to rebuild full context and brief the user on where things stand. Do not start building.

## Protocol

Execute in order, do not skip steps.

### Step 1 - Read the core context

Read these in parallel:
1. `CLAUDE.md` - conventions and standards
2. `STATE.md` - live state of the project
3. `TASKS.md` - the backlog

If any of the three is missing, stop and tell the user. Something is wrong: the project may not be scaffolded, or the working directory is wrong.

### Step 2 - Read the reference and the plan

Read `docs/assignment-brief.md` (the assignment and dataset facts). Read `PLAN.md` if it exists (the build plan).

### Step 3 - Reality check

Use Glob to check the real state of the repo against what `STATE.md` claims:
- Do `backend/`, `frontend/`, `mcp/` exist?
- Does the file tree match the phase described in `STATE.md`?

If `STATE.md` and reality diverge, note it as an inconsistency in the briefing.

### Step 4 - Brief the user

Present a short briefing in this shape:
- Where we stopped (2-3 lines from the last session in `STATE.md`)
- Current phase
- Next steps (from `STATE.md` and `TASKS.md`)
- Open questions and risks
- Inconsistencies detected (only if Step 3 found any)

### Step 5 - Wait for direction

Do not start the next task automatically. Wait for the user to say what to do.

## Rules

- Read-only. This skill does not modify any file.
- Be concise. The briefing is to re-establish context in about 20 seconds of reading.
- If `STATE.md` and the real repo diverge, say so plainly.
- Do not summarize the whole project, just what is needed to resume.

## When NOT to use

- The user already gave a concrete task. Just do the task.
- `CLAUDE.md` or `STATE.md` do not exist yet. The project is not scaffolded.
