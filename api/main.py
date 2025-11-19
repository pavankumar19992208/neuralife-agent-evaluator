import os
import uuid
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

APP_VERSION = "0.1.0"
DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Neuralife Agent Evaluator API", version=APP_VERSION)

# Mount UI if present
UI_DIR = os.path.join(os.path.dirname(__file__), "ui")
if os.path.isdir(UI_DIR):
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

class EvalRequest(BaseModel):
    agent_archive_path: str
    suite: str = "all"
    run_id: Optional[str] = None

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
    return {"job_id": job_id, "message": "welcome run queued/completed", "report_path": f"/data/{job_id}_report.json"}

@app.post("/evaluate")
def evaluate(req: EvalRequest):
    job_id = req.run_id or str(uuid.uuid4())
    placeholder = {
        "job_id": job_id,
        "agent": req.agent_archive_path,
        "suite": req.suite,
        "status": "queued",
        "schema_version": 1
    }
    path = os.path.join(DATA_DIR, f"{job_id}_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(placeholder, f, indent=2)
    return {"job_id": job_id, "report_path": path}

@app.get("/trace/{job_id}")
def get_trace(job_id: str):
    trace_path = os.path.join(DATA_DIR, f"{job_id}_trace.json")
    if not os.path.exists(trace_path):
        return {"error": "trace not found", "job_id": job_id}
    with open(trace_path, "r", encoding="utf-8") as f:
        return json.load(f)