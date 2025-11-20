#!/usr/bin/env python3
import argparse, os, shutil, subprocess, uuid, json, time
from pathlib import Path

DATA_DIR = os.environ.get("NLE_DATA_DIR", "/data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

def extract_archive(archive_path: str, dest: str):
    shutil.unpack_archive(archive_path, dest)

def docker_available() -> bool:
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True, timeout=5)
        return True
    except Exception:
        return False

def run_in_docker(workdir: str, cmd: str, job_id: str, timeout_s: int, memory: str, cpus: str):
    container_name = f"nle_sandbox_{job_id}"
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "--cpus", str(cpus),
        "--memory", memory,
        "--network", "none",
        "-v", f"{workdir}:/agent:ro",
        "python:3.11-slim",
        "bash", "-lc", f"cd /agent && {cmd}"
    ]
    start = time.time()
    try:
        proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout_s)
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_seconds": round(time.time() - start, 3),
        }
    except subprocess.TimeoutExpired as e:
        try: subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, timeout=5)
        except Exception: pass
        return {
            "exit_code": -1,
            "stdout": (getattr(e, "stdout", "") or ""),
            "stderr": (getattr(e, "stderr", "") or "") + f"\nTIMEOUT after {timeout_s}s",
            "duration_seconds": timeout_s,
        }

def parse_tool_calls(stdout: str):
    out = []
    for line in stdout.splitlines():
        s = line.strip()
        if s.startswith("{") and '"tool_calls"' in s:
            try:
                obj = json.loads(s)
                if isinstance(obj, dict) and "tool_calls" in obj:
                    out += obj.get("tool_calls") or []
            except json.JSONDecodeError:
                pass
    return out

def write_trace(job_id: str, archive_path: str, cmd: str, result: dict, workdir: str) -> str:
    trace = {
        "job_id": job_id,
        "archive_path": os.path.abspath(archive_path),
        "command": cmd,
        "duration_seconds": result.get("duration_seconds"),
        "exit_code": result.get("exit_code"),
        "stdout_snippet": (result.get("stdout") or "")[:4000],
        "stderr_snippet": (result.get("stderr") or "")[:4000],
        "tool_calls": parse_tool_calls(result.get("stdout") or ""),
        "workdir": workdir,
        "created_at": time.time(),
    }
    out_path = os.path.join(DATA_DIR, f"{job_id}_trace.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)
    return out_path

def run_job(archive: str, cmd: str, timeout: int, memory: str, cpus: str):
    if not docker_available():
        raise RuntimeError("Docker not available. Ensure docker.sock is mounted and docker CLI installed.")
    job_id = str(uuid.uuid4())
    workdir = os.path.join(DATA_DIR, "work", job_id)  # host-mapped path
    Path(workdir).mkdir(parents=True, exist_ok=True)

    try:
        extract_archive(archive, workdir)
    except Exception as e:
        err_path = os.path.join(DATA_DIR, f"{job_id}_trace.json")
        with open(err_path, "w") as f:
            json.dump({"job_id": job_id, "error": f"extract failed: {e}", "archive": os.path.abspath(archive)}, f, indent=2)
        return job_id, err_path

    try:
        result = run_in_docker(workdir, cmd, job_id, timeout_s=timeout, memory=memory, cpus=cpus)
    except Exception as e:
        result = {"exit_code": -2, "stdout": "", "stderr": f"runner exception: {e}", "duration_seconds": 0}

    trace_path = write_trace(job_id, archive, cmd, result, workdir)
    return job_id, trace_path

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True)
    p.add_argument("--cmd", default="python agent_main.py")
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--memory", default="256m")
    p.add_argument("--cpus", default="0.5")
    args = p.parse_args()
    jid, path = run_job(args.archive, args.cmd, args.timeout, args.memory, args.cpus)
    print(json.dumps({"job_id": jid, "trace_path": path}))
