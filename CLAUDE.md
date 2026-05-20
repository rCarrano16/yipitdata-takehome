# CLAUDE.md

Conventions and standards for this project. Always read this first.

## Project

A full-stack application for the YipitData Senior Software Engineer assignment. It shows quarterly KPI estimates for time-constrained public-market investors, served through two channels: a web frontend for human users and an MCP (Model Context Protocol) server for AI agents. The product thesis is glanceability: the user sees trends at a glance (history vs QTD) and drills down for detail when needed. The app saves investors the effort of digging through raw estimates.

This code is reviewed and extended in a 60-minute live coding session, so every line must be simple enough to explain and defend without notes.

## Key technical challenges

The build must address these deliberately. "Effectiveness of architecture in addressing key technical challenges" is the first evaluation criterion.

1. The QTD / as-of point-in-time snapshot model. A QTD estimate is not a single value, it is a series of intra-quarter snapshots, each stamped with an `as_of` date.
2. One shared data API serving both the frontend and the MCP server, without duplicating query logic. The MCP layer and the REST layer call the same service layer.
3. MCP tools that an LLM can use naturally, with names, descriptions, and parameters that make sense from the model's perspective.
4. Fast read performance for the glanceable UX, since the users are time-constrained.

## Prime directive

AI writes simple, conventional, readable code. No clever abstractions, no premature generality, no metaprogramming. When in doubt, pick the boring, obvious solution. The reason is concrete: this code is defended and extended live, so it must be fully owned and explainable.

## Workflow rules

- The application core is built in the main thread, where every decision is visible. It is never delegated to opaque build-subagents.
- Subagents are used only for research and for reviewing finished code.
- Planning is done with native Plan mode, producing a `PLAN.md`.
- Every work session opens with the `start-session` skill and closes with the `end-session` skill.
- Use built-in tools where they fit: Plan mode, the Explore agent, `/security-review`.

## End-of-phase report

When a phase of the build PLAN is implemented, do the following in order, and only then run `end-session`:

1. Run the phase's `Verify` step and show the real output. Do not claim a phase passed, prove it.
2. Give a short educational summary of what was built. Descriptive and easy to understand. Explain every technical term and the basics of each stack or tool involved, so it can be followed without prior knowledge of that tool. Cover what was done and why. Keep it concise: define the terms, but do not over-extend.
3. Give a test checklist for the user: concrete, ordered steps to verify the phase by hand, each with the exact command and its expected result.

This report is delivered in the chat for the user to read and act on within the session. `end-session` is the final handoff and runs only after this report, with nothing left to do after it.

## Development log

`DEVLOG.md` is a chronological, educational record of how the project is built. It exists so the work can be reviewed afterward, the workflow improved, and the study needs made explicit. It is internal and gitignored.

Maintain it as work happens:
- When you finish a meaningful component, make a non-obvious decision, hit a friction point, or abandon an approach, append a brief dated note to `DEVLOG.md` right then.
- Write educationally: explain the what and the why, so that reading the log back is itself study.
- The `end-session` skill finalizes each session's entry with the retrospective sub-sections (decisions, friction, to study, workflow notes).
- Entries are chronological, one per session, oldest first, append-only. The format is defined at the top of `DEVLOG.md`.

## Target app layout

Refined in the build PLAN. The three application directories below do not exist yet, they are created by the build.

- `backend/` FastAPI service. SQLAlchemy models, routers, a KPI/QTD service layer, a seed script.
- `frontend/` React + TypeScript single-page app. Charts, search, date-range filter, export.
- `mcp/` FastMCP server exposing the same data API as MCP tools.
- `data/` the CSV seed (`kpi_sample_2000.csv`).
- `docs/` reference docs and the architecture diagram.

## Per-area standards

Concise principles. Details are refined in the build PLAN.

**Backend.** Python 3.12 or newer. Type hints everywhere. Pydantic models for request and response bodies. Thin routers that call a service layer, no business logic in routers. SQLAlchemy 2.0 style. `ruff` for lint and format. Structured logging, no bare `print`.

**Frontend.** TypeScript in strict mode. Function components and hooks only. One typed API client module, all fetches go through it. Local state by default, shared state only when genuinely shared. Plain, readable JSX. The UX supports a glance-level overview and a drill-down to the detailed chart.

**MCP.** Discoverable, LLM-friendly tools. Clear names. Docstrings written as instructions to an LLM. Explicit typed parameters. Small, focused tools. The MCP layer reuses the backend service layer, it never re-implements queries.

**Data and security.** No secrets in code, configuration through `.env`. Parameterized queries only. Validate all external input with Pydantic. Authentication is not required by the assignment, so do not build it, but do not expose write endpoints carelessly.

**Observability.** Structured JSON logs. Request-logging middleware. A `/health` endpoint. Basic request timing. The README must describe an observability, monitoring, and auditing plan even where it is not fully implemented, since it is graded.

## QTD conceptual core

For each (company, KPI) pair there is a time series. Historical estimates are one value per closed fiscal quarter. QTD (quarter-to-date) estimates cover the in-progress quarter: instead of one value, there are several snapshots, each stamped with an `as_of` date, showing how the estimate evolved during the quarter. The current QTD value of a series is the snapshot with the latest `as_of`. Modeling this correctly is the heart of the assignment. Full data facts are in `docs/assignment-brief.md`.

## Deliverables checklist

- Working full-stack application codebase.
- Working MCP server, plus instructions to connect it from an AI client.
- `README.md` with run instructions and the key architecture and design decisions.
- An architecture diagram. Use Mermaid in the README or in `docs/`, so it stays versionable and editable during the live session.
- A brief outline of future improvements.

## Conventions

- No em-dash and no en-dash anywhere: code, comments, docs, commit messages. Use a comma, a period, parentheses, or an ASCII hyphen.
- Conventional Commits for commit messages.
- ASCII-only identifiers.

## Out of scope

Authentication, real-time streaming, multi-tenancy.
