---
name: end-session
description: Use this at the END of a work session on the yipitdata-takehome project for a clean context handoff. Updates TASKS.md and rewrites STATE.md. Triggers include "end session", "wrap up", "handoff", "stopping for now", "that is it for today", or invoking /end-session.
---

# Skill: end-session

You are closing a work session on the yipitdata-takehome project. Your job is to leave a clean handoff so the next session resumes without losing context.

## Protocol

Execute in order.

### Step 1 - Review what was done

Look at `git status` and `git diff`, and at the conversation. Build an accurate picture of what changed this session. Do not invent progress.

### Step 2 - Update TASKS.md

Check off completed items. Add any new tasks discovered this session. Never delete an item.

### Step 3 - Update CLAUDE.md if needed

If a convention or standard changed this session, update `CLAUDE.md` to match. If nothing changed, skip this step.

### Step 4 - Rewrite STATE.md

Rewrite `STATE.md` in full, do not append. Keep it around 100 lines. Sections:
- Status and phase
- Last session (2-3 lines on what was done)
- Next step
- Open questions and risks
- Decisions log

### Step 5 - Suggest a commit

Suggest a Conventional Commits message for the session's work. Do not commit without the user's OK.

### Step 6 - Summary

Give a three-line summary: what changed, and what is next.

## Rules

- `STATE.md` is rewritten, not appended. It is a snapshot, not a log.
- Do not invent progress. If something is half-done, say it is half-done.
- Never commit without explicit confirmation from the user.
- No em-dash or en-dash.

## When NOT to use

- In the middle of an unfinished task. Finish or reach a clean stopping point first.
- Nothing changed since the last handoff.
