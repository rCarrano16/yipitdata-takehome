---
name: end-session
description: Use this at the END of a work session on the yipitdata-takehome project for a clean context handoff. Finalizes the DEVLOG, updates TASKS.md, and rewrites STATE.md. Triggers include "end session", "wrap up", "handoff", "stopping for now", "that is it for today", or invoking /end-session.
---

# Skill: end-session

You are closing a work session on the yipitdata-takehome project. Your job is to leave a clean handoff so the next session resumes without losing context, and to finalize the educational record of this session.

## Protocol

Execute in order.

### Step 1 - Review what was done

Look at `git status` and `git diff`, and at the conversation. Build an accurate picture of what changed this session, in chronological order, including friction points and dead ends. Do not invent progress.

### Step 2 - Finalize the DEVLOG entry

Finalize this session's entry in `DEVLOG.md`. If brief notes were appended during the session, consolidate them. Otherwise reconstruct the session from the conversation. The entry must have all sub-sections, per the format at the top of `DEVLOG.md`:
- What was done (chronological, educational: explain the what and the why)
- Decisions and why
- Friction and dead ends
- To study
- Workflow notes

Write educationally, so reading the entry back is itself study. The log is append-only, never rewrite past entries.

### Step 3 - Update TASKS.md

Check off completed items. Add any new tasks discovered this session. Never delete an item.

### Step 4 - Update CLAUDE.md if needed

If a convention or standard changed this session, update `CLAUDE.md` to match. If nothing changed, skip this step.

### Step 5 - Rewrite STATE.md

Rewrite `STATE.md` in full, do not append. Keep it around 100 lines. Sections:
- Status and phase
- Last session (2-3 lines on what was done)
- Next step
- Open questions and risks
- Decisions log

### Step 6 - Suggest a commit

Suggest a Conventional Commits message for the session's work. Do not commit without the user's OK.

### Step 7 - Summary

Give a three-line summary: what changed, and what is next.

## Rules

- `STATE.md` is rewritten, not appended. It is a snapshot, not a log.
- `DEVLOG.md` is append-only and chronological. Never rewrite or delete past entries.
- Do not invent progress. If something is half-done, say it is half-done.
- Never commit without explicit confirmation from the user.
- No em-dash or en-dash.

## When NOT to use

- In the middle of an unfinished task. Finish or reach a clean stopping point first.
- Nothing changed since the last handoff.
