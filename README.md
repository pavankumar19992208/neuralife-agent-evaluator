# Neuralife Agent Evaluator (Day 0 Skeleton)

Evaluator platform to run and score AI agents across reasoning, tool usage, safety, robustness. This is the initial scaffold.

## Status

Day 0 skeleton: API service, sample tests, grader prompt templates, placeholder UI, sandbox stub.

## Quick Start (Windows PowerShell)

```powershell
make build
make up
# New terminal
make run-welcome
```

Visit: http://localhost:8000/health and http://localhost:8080/ (UI placeholder).

## Services (docker-compose)

- api: FastAPI evaluator API
- sandbox: future restricted execution environment
- ui: static placeholder

## Endpoints

- GET /health
- POST /run-welcome
- POST /evaluate (stub)
- GET /trace/{job_id} (placeholder)

## Directory Overview

- api/: FastAPI service
- tests/: YAML test suite examples
- graders/: Prompt templates for LLM graders
- sandbox/: Runner placeholder docs
- ui/: Static placeholder page
- docs/: Architecture notes
- data/: Runtime artifacts (reports, traces)

## Next Milestones

1. Sandbox runner execution with resource limits (Day 1)
2. Test suite loader + executor (Day 2)
3. Grader integration & score aggregation (Day 3)
4. Trace capture & observability endpoint (Day 4)

## Open Decisions

- Demo agent domain (home automation vs shipping coordinator)
- Grader provider (Gemini/OpenAI/mock)
- UI framework (static HTML now; React/Tailwind later)

## License

(Choose a license before public release; e.g., MIT.)
