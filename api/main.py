import os, uuid, json, subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException ,BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from api.tasks.sandbox_job import start_sandbox_job

APP_VERSION = "0.1.0"
DATA_DIR = os.getenv("DATA_DIR", "/data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Neuralife Agent Evaluator API", version=APP_VERSION)

# Serve static UI at /ui
BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"

if UI_DIR.exists() and UI_DIR.is_dir():
    app.mount("/ui", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
else:
    print(f"WARNING: UI directory not found at {UI_DIR}")

class EvalRequest(BaseModel):
    agent_archive_path: str
    suite: str = "all"
    run_id: Optional[str] = None

class StartEvalRequest(BaseModel):
    archive_path: str
    cmd: str = "python agent_main.py"
    timeout: int = 30
    memory: str = "256m"
    cpus: str = "0.5"
class RunEvalRequest(BaseModel):
    raw_results_path: str
@app.get("/")
def root():
    return RedirectResponse(url="/ui/")

@app.get("/health")
def health():
    return {"status": "ok", "service": "neuralife-evaluator", "version": APP_VERSION}

@app.get("/welcome")
def welcome():
    return {"message": "Neuralife Agent Evaluator running", "version": APP_VERSION}

def run_pipeline_task(raw_path: str):
    """Background task to run the evaluation pipeline script."""
    try:
        # Assuming evaluation_pipeline.py is in /app/evaluation/
        # and python is available in path
        cmd = ["python", "evaluation/evaluation_pipeline.py", "--data", raw_path]
        print(f"Starting pipeline: {' '.join(cmd)}")
        
        # Fix: Add current directory to PYTHONPATH so 'graders' module is found
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        subprocess.run(cmd, check=True, env=env) # <--- Pass env here
        print(f"Pipeline finished for {raw_path}")
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed: {e}")
    except Exception as e:
        print(f"Error running pipeline: {e}")

@app.post("/run-evaluation")
def run_evaluation(req: RunEvalRequest, background_tasks: BackgroundTasks):
    """Triggers the Day 3 evaluation pipeline."""
    if not os.path.exists(req.raw_results_path):
        raise HTTPException(status_code=404, detail="Raw results file not found")
    
    # Run in background so UI doesn't hang
    background_tasks.add_task(run_pipeline_task, req.raw_results_path)
    
    return {"status": "started", "message": "Evaluation pipeline started in background"}
@app.post("/run-welcome")
def run_welcome():
    job_id = str(uuid.uuid4())
    payload = {"job_id": job_id, "message": "welcome run completed"}
    with open(os.path.join(DATA_DIR, f"{job_id}_report.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return payload

@app.post("/start-eval")
def start_eval(req: StartEvalRequest):
    if not Path(req.archive_path).exists():
        raise HTTPException(status_code=400, detail="archive_path not found on server")
    result = start_sandbox_job(req.archive_path, req.cmd, req.timeout, req.memory, req.cpus)
    return {"status": "completed", **result}

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

# --- NEW DAY 3 ENDPOINTS ---

@app.get("/report-list")
def report_list():
    """Lists all generated evaluation reports."""
    if not os.path.exists(REPORTS_DIR):
        return {"reports": []}
    # FIX: Changed suffix to match pipeline output (_report.json)
    files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith("_report.json")])
    return {"reports": files}

@app.get("/report/{run_id}")
def get_report(run_id: str):
    """Returns the JSON evaluation report."""
    # Handle both full filename or just the ID
    if not run_id.endswith(".json"):
        # FIX: Changed suffix
        filename = f"{run_id}_report.json"
    else:
        filename = run_id
        
    path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/report-html/{run_id}")
def get_report_html(run_id: str):
    """Returns the HTML evaluation report for rendering in browser."""
    # Extract ID if filename passed
    # FIX: Changed suffix replacements
    clean_id = run_id.replace("_report.json", "").replace("_report.html", "")
    filename = f"{clean_id}_report.html"
    
    path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="HTML Report not found")
            
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())