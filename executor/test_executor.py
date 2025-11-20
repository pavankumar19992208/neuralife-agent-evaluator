import uuid, json, time
from pathlib import Path
from api.tasks.sandbox_job import start_sandbox_job
from tests.loader import load_suite

DATA_DIR = Path("/data")
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def run_suite_from_file(suite_path: str, archive_path: str, cmd: str="python agent_main.py"):
    suite = load_suite(suite_path)
    run_id = str(uuid.uuid4())
    results = {"run_id": run_id, "suite": suite.suite, "tests": []}
    for tc in suite.tests:
        t0 = time.time()
        res = start_sandbox_job(archive_path, cmd)
        job_id = res.get("job_id")
        trace_path = res.get("trace_path")
        trace = {}
        try:
            trace = json.loads(open(trace_path).read())
        except Exception:
            pass
        duration = time.time() - t0
        results["tests"].append({
            "test_id": tc.id,
            "prompt": tc.prompt,
            "grader": tc.grader,
            "job_id": job_id,
            "trace_path": trace_path,
            "trace": trace,
            "duration": duration
        })
    out = REPORTS_DIR / f"{run_id}_raw_results.json"
    out.write_text(json.dumps(results, indent=2))
    return out