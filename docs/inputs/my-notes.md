# My Hackathon Notes

Write rough ideas, priorities, constraints, and extra notes here before kickoff and anytime new information arrives during the hackathon.

## Kickoff Notes & Idea

- **Core Pitch:** One standard AED schema + automatic harvest of all AED data from dane.gov.pl (+ OSM) merged into one national dataset, served through a dane.gov.pl-compatible API and shown inside a local fork of the dane.gov.pl portal.
- **Target Persona:** dane.gov.pl operator / AED data owner; consumers: emergency services, developers, public.
- **Key Differentiator:** Runs on the real dane.gov.pl code; schema is the core; per-source coverage report.

## Judging & Demo Priorities

- dane.gov.pl compliance 30%, logo+slogan 25%, schema 10%. Schema is the most important technical piece.

## Constraints & Assumptions

- Deadline 2026-11-22 11:00, code freeze 09:00.
- Fork of dane.gov.pl copied into `dane-gov-pl/` (local only, heavy stack: ES, RabbitMQ, Redis, Celery, Angular).
- Public APIs: api.dane.gov.pl/1.4, OSM Overpass. No keys needed.

## Extra Notes Added Mid-Hackathon

<!-- Add dated notes below, then invoke hackathon-update-plan so docs/04-decisions.md and tasks stay synced -->
- `[2026-11-21 18:00]` Kickoff recorded as DEC-002.
