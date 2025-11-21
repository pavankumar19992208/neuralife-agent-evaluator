import argparse
import json
import os
import sys
from datetime import datetime

# Ensure we can import graders
sys.path.append(os.getcwd())

try:
    from graders.grader_engine import grade
except ImportError:
    # Fallback if running from different directory
    sys.path.append(os.path.join(os.getcwd(), ".."))
    from graders.grader_engine import grade

REPORTS_DIR = os.environ.get("DATA_DIR", "data") + "/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def generate_html_report(run_id, results, overall_score):
    """Generates a simple HTML scorecard."""
    rows = ""
    for r in results:
        rows += f"""
        <tr>
            <td>{r['test_id']}</td>
            <td>{r['prompt'][:50]}...</td>
            <td>{r['score']}/5</td>
            <td>{r['reason']}</td>
            <td>{r['actual_output'][:100]}...</td>
        </tr>
        """
    
    html = f"""
    <html>
    <head>
        <title>Eval Report: {run_id}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .score {{ font-size: 2em; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Evaluation Report</h1>
        <p>Run ID: <strong>{run_id}</strong></p>
        <div class="score">Overall Score: {overall_score}/100</div>
        <br/>
        <table>
            <tr>
                <th>ID</th>
                <th>Prompt</th>
                <th>Score</th>
                <th>Reasoning</th>
                <th>Agent Output</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return html

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to raw results JSON")
    args = parser.parse_args()

    if not os.path.exists(args.data):
        print(f"Error: File not found {args.data}")
        sys.exit(1)

    with open(args.data, "r") as f:
        raw_data = json.load(f)

    run_id = raw_data.get("run_id", "unknown_run")
    print(f"🚀 Starting Evaluation for: {run_id}")

    graded_results = []
    total_score = 0
    count = 0

    # --- ADAPTER LOGIC ---
    # Detect if this is Day 2 "Raw Results" (list of tests) or Day 3 "Eval Set" (list of cases)
    items_to_grade = []
    
    if "tests" in raw_data:
        print(f"   -> Detected Day 2 Raw Results format ({len(raw_data['tests'])} tests)")
        for t in raw_data["tests"]:
            # Extract output from the trace stdout
            trace = t.get("trace", {})
            stdout = trace.get("stdout_snippet", "")
            # Simple cleanup: remove the file listing if present
            if "total 4" in stdout:
                stdout = stdout.split("total 4")[1]
            
            items_to_grade.append({
                "id": t.get("test_id", "unknown"),
                "prompt": t.get("prompt", ""),
                "actual_output": stdout.strip()
            })
            
    elif "eval_cases" in raw_data:
        print(f"   -> Detected Day 3 Eval Set format ({len(raw_data['eval_cases'])} cases)")
        for t in raw_data["eval_cases"]:
            # Assuming standard ADK format
            items_to_grade.append({
                "id": t.get("eval_id", "unknown"),
                "prompt": t.get("conversation", [{}])[0].get("user_content", {}).get("parts", [{}])[0].get("text", ""),
                "actual_output": t.get("conversation", [{}])[-1].get("final_response", {}).get("parts", [{}])[0].get("text", "")
            })
    else:
        print("❌ Error: Unknown JSON format. Expected 'tests' or 'eval_cases' key.")
        sys.exit(1)

    # --- GRADING LOOP ---
    for item in items_to_grade:
        print(f"   Grading {item['id']}...", end="", flush=True)
        
        # Call Gemini Judge
        score, reason = grade(item['prompt'], item['actual_output'])
        
        print(f" Score: {score}/5")
        
        graded_results.append({
            "test_id": item['id'],
            "prompt": item['prompt'],
            "actual_output": item['actual_output'],
            "score": score,
            "reason": reason
        })
        total_score += score
        count += 1

    # Calculate final metrics
    final_score = 0
    if count > 0:
        # Normalize 5-point scale to 100-point scale
        final_score = int((total_score / (count * 5)) * 100)

    print(f"\n✅ Evaluation Complete!")
    print(f"📊 Overall Score: {final_score}/100")

    # Save Reports
    report_base = os.path.join(REPORTS_DIR, f"{run_id}")
    
    # 1. JSON Report
    json_report = {
        "run_id": run_id,
        "final_score": final_score,
        "details": graded_results
    }
    with open(f"{report_base}_report.json", "w") as f:
        json.dump(json_report, f, indent=2)

    # 2. HTML Report
    html_content = generate_html_report(run_id, graded_results, final_score)
    with open(f"{report_base}_report.html", "w") as f:
        f.write(html_content)

    print(f"📄 Reports saved to: {REPORTS_DIR}")

if __name__ == "__main__":
    main()