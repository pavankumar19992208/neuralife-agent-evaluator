# Neuralife Agent Evaluator

A lightweight, dockerized framework to run, observe, and grade LLM agents in a reproducible, sandboxed way. Built to demo enterprise-ready evaluation with clear traces, YAML test suites, and pluggable LLM graders.

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.1x-teal">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-blue">
  <img alt="Deploy" src="https://github.com/pavankumar19992208/neuralife-agent-evaluator/actions/workflows/deploy.yml/badge.svg">
</p>

## What it does (MVP)

- FastAPI backend with endpoints to run and evaluate jobs.
- Static UI (placeholder) served at /ui with live health check.
- Persistent outputs in ./data (JSON report/trace).
- Docker-first dev and a one-click GitHub Actions deploy to EC2.

Roadmap highlights:

- Secure sandbox runner (no-network, CPU/RAM/time limits).
- YAML test suites (Correctness, Reasoning, Tooling, Safety, Robustness).
- Pluggable LLM graders (Gemini/OpenAI/mock) with structured scores.
- Parallel sub-agent execution with a job queue.
- Trace timeline and report dashboard.

---

## Repository layout

```
neuralife-agent-evaluator/
├─ api/                 # FastAPI service
│  ├─ main.py
│  ├─ Dockerfile
│  └─ requirements.txt
├─ ui/                  # Static UI (served at /ui)
│  └─ index.html
├─ data/                # Job outputs (mounted volume)
├─ docker-compose.yml   # Single-container stack (API + static UI)
└─ .github/workflows/   # CI/CD (deploy to EC2)
   └─ deploy.yml
```

## Quickstart (Docker, local or EC2)

Prereqs: Docker + Docker Compose.

```bash
# from repo root
docker compose build
docker compose up -d
# health
curl http://localhost:8000/health
# demo job
curl -X POST http://localhost:8000/run-welcome
# open UI
# local:  http://localhost:8000/ui/
# on EC2: http://<EC2_PUBLIC_IP>:8000/ui/
```

Outputs:

- A POST to /run-welcome creates data/<job_id>\_report.json.

Tip: If Compose warns about “version” being obsolete, you can remove the top-level `version:` key.

## API endpoints

- GET /health → {"status":"ok", ...}
- GET /welcome → simple welcome payload
- GET / → redirects to /ui
- POST /run-welcome → creates a sample report file in ./data
- POST /evaluate → placeholder for Day 1+ evaluator pipeline
- GET /trace/{job_id} → returns trace JSON if present

Example:

```bash
curl -s -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"agent_archive_path":"demo/agent.py","suite":"all"}'
```

## CI/CD: Deploy to EC2 (GitHub Actions)

The workflow at .github/workflows/deploy.yml:

- Triggers on push to main/master and manual runs.
- SSHes into the EC2 host, resets working copy to origin/main (or master), rebuilds, and restarts via Docker Compose.

Setup:

1. On EC2 (Ubuntu 22.04): install Docker + Compose; add user to docker group.
2. Security Group: allow TCP 22 (SSH) and 8000 (API) from your IP.
3. GitHub repo secrets:
   - EC2_SSH_KEY: contents of your .pem
   - EC2_HOST: public IPv4 of instance
   - EC2_USER: ubuntu

Deploy:

- Push to main/master, or run the workflow from the Actions tab.
- Verify on server:
  ```bash
  docker compose ps
  curl http://localhost:8000/health
  ```

## Troubleshooting

- 404 on /health: ensure api/main.py endpoints are implemented and container is healthy.
- 405 on /run-welcome: use POST, not GET.
- Ports blocked externally: open 8000 in the EC2 Security Group for your IP.
- Logs:
  ```bash
  docker compose logs api --tail=100
  ```

## Day 1 plan (next)

- Add sandbox runner (Docker-in-Docker or Docker SDK) with resource limits.
- Implement job queue and parallel sub-agent execution (configurable concurrency).
- YAML test suite loader and mock grader (LLM adapter stub).
- Persisted evaluation reports and traces per job.

---

MIT-style license (add if desired). Contributions welcome.
