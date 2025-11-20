import os
import uuid
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.tasks.sandbox_job import start_sandbox_job

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
APP_VERSION = "0.2.0"

DATA_DIR = Path(os.getenv("NLE_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Neuralife Agent Evaluator API", version=APP_VERSION)

# ---------------------------------------------------------
# UI MOUNT
# ---------------------------------------------------------
UI_DIR = Path(__file__).parent / "ui"
if UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")


# ---------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------
class EvalRequest(BaseModel):
    agent_archive_path: str
    suite: str = "all"
    run_id: Optional[str] = None


class StartEvalRequest(BaseModel):
    archive_path: str     # /data/agents/home_automation_agent.tar.gz
    cmd: str = "python agent_main.py"
    timeout: int = 30
    memory: str = "256m"
    cpus: str = "0.5"


# ---------------------------------------------------------
# ROOT + HEALTH
# ---------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse(url="/ui/")


@app.get("/health")
def health():
    return {"status": "ok", "service": "neuralife-evaluator", "version": APP_VERSION}


@app.get("/welcome")
def welcome():
    return {"message": "Neuralife Agent Evaluator running", "version": APP_VERSION}


# ---------------------------------------------------------
# DAY 0 — WELCOME REPORT
# ---------------------------------------------------------
@app.post("/run-welcome")
def run_welcome():
    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id, "message": "welcome run completed"}
    with open(DATA_DIR / f"{job_id}_report.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload


# ---------------------------------------------------------
# DAY 1 — START SANDBOX EVAL (ASYNC)
# ---------------------------------------------------------
@app.post("/start-eval")
def start_eval(req: StartEvalRequest, background_tasks: BackgroundTasks):
    archive_path = Path(req.archive_path)
    if not archive_path.exists():
        raise HTTPException(status_code=400, detail=f"archive_path not found: {archive_path}")

    background_tasks.add_task(
        start_sandbox_job,
        req.archive_path,
        req.cmd,
        req.timeout,
        req.memory,
        req.cpus
    )

    return {
        "status": "accepted",
        "message": "Evaluation started.",
        "hint": "Poll /trace-list and /trace/{job_id} for results."
    }


# ---------------------------------------------------------
# TRACE LIST & TRACE FETCH
# ---------------------------------------------------------
@app.get("/trace-list")
def trace_list():
    files = sorted([p.name for p in DATA_DIR.glob("*_trace.json")])
    return {"traces": files}


@app.get("/trace/{job_id}")
def get_trace(job_id: str):
    trace_path = DATA_DIR / f"{job_id}_trace.json"
    if not trace_path.exists():
        raise HTTPException(status_code=404, detail="trace not found")
    with open(trace_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# LEGACY EVALUATE ENDPOINT (Keeps your Day 0 Routes)
# ---------------------------------------------------------
@app.post("/evaluate")
def evaluate(req: EvalRequest):
    job_id = req.run_id or str(uuid.uuid4())
    report = {
        "job_id": job_id,
        "agent": req.agent_archive_path,
        "suite": req.suite,
        "status": "queued",
        "schema_version": 1
    }
    path = DATA_DIR / f"{job_id}_report.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return {"job_id": job_id, "report_path": str(path)}
