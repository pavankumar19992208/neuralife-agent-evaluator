import os, subprocess, json
from pathlib import Path

RUNNER_PY = Path("/app/runner/run_agent_in_sandbox.py")

def start_sandbox_job(archive_path: str, cmd: str = "python agent_main.py", timeout: int = 30, memory: str = "256m", cpus: str = "0.5"):
    if not RUNNER_PY.exists():
        raise FileNotFoundError(f"Runner not found at {RUNNER_PY}")
    proc = subprocess.run(
        ["python", str(RUNNER_PY), "--archive", archive_path, "--cmd", cmd, "--timeout", str(timeout), "--memory", memory, "--cpus", str(cpus)],
        capture_output=True, text=True
    )
    try:
        return json.loads(proc.stdout.strip())
    except Exception:
        return {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
