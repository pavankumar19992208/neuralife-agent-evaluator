# Neuralife Agent Evaluator - Architecture (Day 0 Draft)

## Core Components

- API Service (FastAPI): run management, health, evaluation stubs, trace retrieval.
- Sandbox Runner (future): executes agent code in restricted container, enforces limits.
- Grader Layer: LLM or rule-based graders produce scored JSON per test.
- Test Suite Loader: parses YAML test definitions under `tests/`.
- Trace & Artifact Store: JSON event sequences + generated reports in `/data`.
- UI (placeholder now): will evolve into dashboard for suites, scores, timeline.

## Data Models (Initial)

**Test YAML** fields in samples: `suite`, `description`, `tests[]` each with `id`, `prompt`, optional expectations (keywords, expected_tool), `grader`.
**Evaluation Report (future)**: `job_id`, `agent`, `suite`, `status`, `start_time`, `end_time`, `grade_breakdown[]`, `resource_usage`, `artifacts[]`, `metrics{}`.
**Trace Event**: `ts`, `sequence`, `type`, `actor`, `content`, `metadata`, `correlation_id`.

## Run Flow (Target)

1. User submits evaluation request via `/evaluate`.
2. API schedules sandbox run (future background task/queue).
3. Sandbox executes test harness, emits events -> trace file.
4. Graders process outputs -> score JSON.
5. Aggregation builds `evaluation_report.json`.
6. UI queries `/trace/{job_id}` and report endpoint.

## Isolation & Security (Roadmap)

- Docker resource limits: `--cpus`, memory, timeouts.
- No outbound network by default; controlled tool proxies later.
- Artifact sanitization and separation.

## Next Milestones

- Day 1: Implement sandbox execution, resource caps.
- Day 2: YAML loader & test executor bridging agent I/O.
- Day 3: Grader integration (LLM + mock).
- Day 4: Full trace capture & API endpoint refinement.

## Open Questions

- Initial demo scenario selection (home automation vs shipping).
- Grader provider (Gemini vs mock vs OpenAI).
- UI technology (static HTML vs React/Tailwind SPA).
