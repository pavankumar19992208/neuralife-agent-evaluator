import argparse
import json
from pathlib import Path
from graders.grader_engine import grade
import statistics
import time
import os
import sys

# Weights defined in your project spec
WEIGHTS = {
    "correctness": 0.35,
    "reasoning": 0.25,
    "tool_usage": 0.20,
    "safety": 0.15,
    "robustness": 0.05
}

DATA_DIR = Path(os.environ.get("NLE_DATA_DIR", "/data"))
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def grade_testcase(test):
    """
    Runs all rubrics against a single test case.
    """
    prompt = test.get("prompt")
    trace = test.get("trace", {})
    response = trace.get("stdout_snippet", "")
    
    # Handle expected output format
    tc_expected = test.get("expected", None)
    expected_keywords = None
    if isinstance(tc_expected, (list, dict)):
        expected_keywords = json.dumps(tc_expected)
    elif isinstance(tc_expected, str):
        expected_keywords = tc_expected

    # For tool usage, we look at the structured tool calls
    tool_text = json.dumps(trace.get("tool_calls", []))

    results = {}
    # Run every rubric for every test to get a complete profile
    for rubric in WEIGHTS.keys():
        if rubric == "tool_usage":
            eval_in = tool_text
            exp = test.get("expected_tool", "")
        else:
            eval_in = response
            exp = expected_keywords or test.get("expected", "")
            
        # Call the grader engine
        g = grade(rubric, prompt, eval_in, str(exp or ""))
        results[rubric] = g
    return results

def aggregate_scores(per_test_scores):
    """
    Calculates averages and the final weighted composite score (0-100).
    """
    rubric_scores = {r: [] for r in WEIGHTS.keys()}
    for t in per_test_scores:
        for r, v in t["per_rubric"].items():
            # Ensure we handle cases where score might be missing
            score = v.get("score", 0)
            rubric_scores[r].append(score)

    # Compute averages per rubric
    rubric_avg = {}
    for r, vals in rubric_scores.items():
        rubric_avg[r] = round(statistics.mean(vals), 2) if vals else 0

    # Composite score calculation
    composite = 0.0
    for r, avg in rubric_avg.items():
        composite += (avg/10.0) * WEIGHTS.get(r, 0)
    total_score = round(composite * 100, 2)

    return {
        "rubric_avg": rubric_avg,
        "total_score": total_score
    }

def build_evaluation_report(raw_results_path: Path):
    data = json.loads(raw_results_path.read_text())
    run_id = data.get("run_id") or raw_results_path.stem
    
    print(f"Starting evaluation for Run ID: {run_id}")
    
    per_test_scores = []
    for tc in data.get("tests", []):
        print(f"  Grading test: {tc.get('test_id')}...")
        per_rubric = grade_testcase(tc)
        per_test_scores.append({
            "test_id": tc.get("test_id"),
            "job_id": tc.get("job_id"),
            "trace_path": tc.get("trace_path"),
            "per_rubric": per_rubric
        })

    agg = aggregate_scores(per_test_scores)
    
    report = {
        "run_id": run_id,
        "agent_archive": data.get("tests", [{}])[0].get("trace", {}).get("archive_path", ""),
        "total_score": agg["total_score"],
        "rubric_avg": agg["rubric_avg"],
        "tests": per_test_scores,
        "generated_at": time.time(),
        "weights": WEIGHTS
    }

    # FIX: Updated filenames to match API expectations (_report.json)
    out_json = REPORTS_DIR / f"{run_id}_report.json"
    out_html = REPORTS_DIR / f"{run_id}_report.html"
    
    # Write JSON
    out_json.write_text(json.dumps(report, indent=2))

    # Write HTML Report
    html = f"<html><head><meta charset='utf-8'><title>Evaluation {run_id}</title>"
    html += "<style>body{font-family:sans-serif; max-width:800px; margin:20px auto; padding:20px;} "
    html += "h1{color:#333;} .score{font-size:2em; font-weight:bold; color:#007bff;} "
    html += ".rubric{margin-bottom:10px;} .test-case{border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:5px;}</style>"
    html += "</head><body>"
    
    html += f"<h1>Evaluation Report — {run_id}</h1>"
    html += f"<p><strong>Total Composite Score:</strong> <span class='score'>{report['total_score']}/100</span></p>"
    
    html += "<h2>Rubric Averages (1-10)</h2><ul>"
    for r, a in report["rubric_avg"].items():
        html += f"<li class='rubric'><strong>{r.capitalize()}:</strong> {a} (Weight: {WEIGHTS[r]})</li>"
    html += "</ul>"
    
    html += "<h2>Detailed Test Results</h2>"
    for t in report["tests"]:
        html += f"<div class='test-case'><h3>Test ID: {t['test_id']}</h3>"
        html += f"<small>Job ID: {t['job_id']}</small><ul>"
        for r, val in t["per_rubric"].items():
            html += f"<li><strong>{r}:</strong> {val.get('score', 0)} — <i>{val.get('notes','')}</i></li>"
        html += "</ul></div>"
        
    html += "<hr>"
    html += f"<p>Reference design document: <code>/mnt/data/Untitled document.pdf</code></p>"
    html += "</body></html>"
    
    out_html.write_text(html)
    return out_json, out_html

def main():
    p = argparse.ArgumentParser()
    # FIX: Changed argument to --data to match api/main.py
    p.add_argument("--data", required=True, help="Path to raw results JSON")
    args = p.parse_args()
    
    raw = Path(args.data)
    if not raw.exists():
        raise SystemExit(f"Raw results file not found: {raw}")
        
    out_json, out_html = build_evaluation_report(raw)
    print(f"\nSuccess! Reports generated:\nJSON: {out_json}\nHTML: {out_html}")

if __name__ == "__main__":
    main()