---
name: hackathon-kickoff
description: >-
  Distill raw hackathon organizer instructions (including long PDFs in docs/inputs/organizer-brief/)
  and user notes (docs/inputs/my-notes.md) into docs/01-brief.md, lightweight global baseline
  docs/02-ui-system.md, AGENTS.md brief, and DEC-001 in docs/04-decisions.md. Use at project
  kickoff before creating the development plan.
---

# Hackathon Kickoff

Transform bulky organizer PDFs and rough personal notes into concise, structured project memory so every future turn stays fast and aligned.

## Steps

1. **Read Raw Inputs Completely**
   - List all files in `docs/inputs/organizer-brief/`, `docs/inputs/ui/`, and read `docs/inputs/my-notes.md`.
   - For long PDFs, read every page in sequential page-range chunks (whatever PDF reading your tool supports, e.g. 10–20 pages per read; fall back to Python text extraction such as `pypdf` if direct reading fails) and keep going until the last page, so judging criteria, deadlines, constraints, and hidden requirements are never missed.
   - Read `docs/01-brief.md`, `docs/02-ui-system.md`, `docs/04-decisions.md`, and `AGENTS.md`.

2. **Clarify Ambiguities Before Locking Scope**
   - If critical ambiguities exist (target demo user flow, judging emphasis, required integrations, deadline/demo slot, or out-of-scope cuts), ask concise targeted questions and wait for answers before finalizing the brief.

3. **Distill Into Project Memory**
   - Get the current date/time from the shell (`date '+%Y-%m-%d %H:%M'`) — never guess timestamps.
   - Write `docs/01-brief.md`:
     - Fill **Timeline** (submission deadline, demo slot/length, code-freeze time — default freeze: 2 hours before the deadline unless the user says otherwise), Problem & Demo Goal, Judging Criteria, numbered Requirements (`REQ-01`, `REQ-02`, ...) with source PDF page/section citations, Core User Flows, MVP Scope, Nice-to-Have, Explicit Out of Scope, and Open Questions/Assumptions.
     - Leave the `Target Task(s)` column as `TBD` — `hackathon-plan` fills it.
   - Update `docs/02-ui-system.md`:
     - Set only the lightweight global UI baseline (app shell, top nav, color/typography tokens, WCAG 2.2 AA light baseline, any assets in `docs/inputs/ui/`). Do **not** design individual task screens yet; per-screen UI design happens per task via `hackathon-ui-design`.
   - Fill in `## Hackathon Project Brief (Fill In At Kickoff)` inside `AGENTS.md`, including the deadline/demo/code-freeze line.
   - Append `DEC-001` in `docs/04-decisions.md` capturing initial MVP scope, timeline, and key assumptions.

4. **Review Gate**
   - Summarize the timeline, distilled MVP scope, requirements table, and any remaining `[OPEN]` questions.
   - Ask the user to approve `docs/01-brief.md` before running `hackathon-plan`.
