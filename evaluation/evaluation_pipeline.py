import argparse
import json
import time
import statistics
from pathlib import Path
from graders.grader_engine import grade

# Weights for the evaluation (Customize as per your PDF plan)
WEIGHTS = {
    "correctness": 0.40,
    "reasoning": 0.30,
    "tool_usage": 0.20,
    "safety": 0.10
}

REPORTS_DIR = Path("data/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def grade_test_case(case):
    """
    Grades a single ADK test case.
    """
    # Extract data from ADK Evalset format
    # Note: ADK structure usually has 'conversation' list
    conversation = case.get("conversation", [])
    
    if not conversation:
        return {}

    # Get the User Input (Prompt)
    user_input = conversation[0].get("user_content", {}).get("parts", [{}])[0].get("text", "")
    
    # Get the Agent Output (Response)
    agent_response = conversation[-1].get("final_response", {}).get("parts", [{}])[0].get("text", "")
    
    # Get Tool Calls (Intermediate Data in ADK)
    tool_calls = conversation[-1].get("intermediate_data", {}).get("tool_uses", [])
    
    # Expected values (usually stored in custom fields or separate config)
    expected_output = case.get("expected_output", "")
    expected_tool = case.get("expected_tool", "")

    scores = {}
    
    # 1. Grade Correctness
    scores["correctness"] = grade("correctness", user_input, agent_response, expected_output)
    
    # 2. Grade Reasoning
    scores["reasoning"] = grade("reasoning", user_input, agent_response)
    
    # 3. Grade Tool Usage (if tools were expected or used)
    if tool_calls or expected_tool:
        scores["tool_usage"] = grade("tool_usage", user_input, json.dumps(tool_calls), expected_tool)
    else:
        scores["tool_usage"] = {"score": 10, "notes": "No tools needed/used"}

    # 4. Grade Safety
    scores["safety"] = grade("safety", user_input, agent_response)

    return scores

def calculate_composite_score(rubric_scores):
    total = 0
    weight_sum = 0
    for k, v in rubric_scores.items():
        if k in WEIGHTS:
            total += v["score"] * WEIGHTS[k]
            weight_sum += WEIGHTS[k]
    return round((total / max(weight_sum, 0.01)) * 10, 2) # Scale to 100

def generate_html_report(run_id, results, final_score):
    html = f"""
    <html>
    <head>
        <title>Google ADK Agent Evaluation - {run_id}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            .score-card {{ background: #f4f4f4; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .pass {{ color: green; }} .fail {{ color: red; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4285F4; color: white; }}
        </style>
    </head>
    <body>
        <h1>Agent Evaluation Report</h1>
        <div class="score-card">
            <h2>Final Score: {final_score}/100</h2>
            <p><strong>Run ID:</strong> {run_id}</p>
            <p><strong>Model:</strong> gemini-2.0-flash (Judge)</p>
        </div>
        
        <table>
            <tr>
                <th>Test Case ID</th>
                <th>Prompt</th>
                <th>Correctness</th>
                <th>Reasoning</th>
                <th>Tool Usage</th>
                <th>Safety</th>
            </tr>
    """
    
    for r in results:
        html += f"""
            <tr>
                <td>{r['id']}</td>
                <td>{r['prompt'][:50]}...</td>
                <td>{r['scores']['correctness']['score']}</td>
                <td>{r['scores']['reasoning']['score']}</td>
                <td>{r['scores']['tool_usage']['score']}</td>
                <td>{r['scores']['safety']['score']}</td>
            </tr>
        """
    
    html += """
        </table>
        <br>
        <p><em>Reference: Google 5-Day AI Agents Intensive PDF (Day 4)</em></p>
    </body>
    </html>
    """
    return html

def main():
    parser = argparse.ArgumentParser(description="Google ADK Agent Evaluator")
    parser.add_argument("--data", required=True, help="Path to integration.evalset.json")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: File {data_path} not found.")
        return

    eval_set = json.loads(data_path.read_text())
    run_id = eval_set.get("eval_set_id", "unknown_run")
    
    print(f"🚀 Starting Evaluation for: {run_id}")
    
    results = []
    all_composite_scores = []

    for case in eval_set.get("eval_cases", []):
        case_id = case.get("eval_id", "unknown")
        print(f"  - Grading Case: {case_id}...")
        
        scores = grade_test_case(case)
        composite = calculate_composite_score(scores)
        all_composite_scores.append(composite)
        
        prompt = case["conversation"][0]["user_content"]["parts"][0]["text"]
        
        results.append({
            "id": case_id,
            "prompt": prompt,
            "scores": scores,
            "composite": composite
        })

    final_avg = round(statistics.mean(all_composite_scores), 2) if all_composite_scores else 0
    
    # Export Reports
    json_out = REPORTS_DIR / f"{run_id}_report.json"
    html_out = REPORTS_DIR / f"{run_id}_report.html"
    
    json_out.write_text(json.dumps(results, indent=2))
    html_out.write_text(generate_html_report(run_id, results, final_avg))
    
    print(f"\n✅ Evaluation Complete!")
    print(f"📊 Overall Score: {final_avg}/100")
    print(f"📄 Reports saved to: {REPORTS_DIR}")

if __name__ == "__main__":
    main()