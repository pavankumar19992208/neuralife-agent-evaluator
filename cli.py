import argparse
from executor.test_executor import run_suite_from_file

def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["run-suite"])
    p.add_argument("--suite", required=True, help="path to suite yaml, e.g. tests/examples/reasoning.yaml")
    p.add_argument("--archive", required=True, help="path to agent archive, e.g. /data/agents/home_automation_agent.tar.gz")
    p.add_argument("--cmd", default="python agent_main.py")
    args = p.parse_args()
    if args.action == "run-suite":
        out = run_suite_from_file(args.suite, args.archive, args.cmd)
        print("Wrote raw results:", out)

if __name__ == "__main__":
    main()