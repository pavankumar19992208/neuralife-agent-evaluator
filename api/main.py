import os, uuid, json
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from api.tasks.sandbox_job import start_sandbox_job

APP_VERSION = "0.1.0"
DATA_DIR = os.getenv("DATA_DIR", "/data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Neuralife Agent Evaluator API", version=APP_VERSION)

# Serve static UI at /ui
UI_DIR = os.path.join(os.path.dirname(__file__), "ui")
if os.path.isdir(UI_DIR):
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

class EvalRequest(BaseModel):
    agent_archive_path: str
    suite: str = "all"
    run_id: Optional[str] = None

class StartEvalRequest(BaseModel):
    archive_path: str                  # e.g. /data/agents/home_automation_agent.tar.gz
    cmd: str = "python agent_main.py"
    timeout: int = 30
    memory: str = "256m"
    cpus: str = "0.5"

@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

@app.get("/health")
def health():
    return {"status": "ok", "service": "neuralife-evaluator", "version": APP_VERSION}

@app.get("/welcome")
def welcome():
    return {"message": "Neuralife Agent Evaluator running", "version": APP_VERSION}

@app.post("/run-welcome")
def run_welcome():
    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id, "message": "welcome run completed"}
    with open(os.path.join(DATA_DIR, f"{job_id}_report.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload

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
    path = os.path.join(DATA_DIR, f"{job_id}_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return {"job_id": job_id, "report_path": path}

@app.post("/start-eval")
def start_eval(req: StartEvalRequest, background_tasks: BackgroundTasks):
    if not Path(req.archive_path).exists():
        raise HTTPException(status_code=400, detail="archive_path not found on server")
    background_tasks.add_task(start_sandbox_job, req.archive_path, req.cmd, req.timeout, req.memory, req.cpus)
    return {"status": "accepted", "hint": "Use /trace-list then /trace/{job_id}"}

@app.get("/trace-list")
def trace_list():
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith("_trace.json")])
    return {"traces": files}

@app.get("/trace/{job_id}")
def get_trace(job_id: str):
    trace_path = os.path.join(DATA_DIR, f"{job_id}_trace.json")
    if not os.path.exists(trace_path):
        raise HTTPException(status_code=404, detail="trace not found")
    with open(trace_path, "r", encoding="utf-8") as f:
        return json.load(f)