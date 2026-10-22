#!/usr/bin/env python3
"""Run /ask-team against fixture projects and check the command it answers.

Each scenario in scenarios/*.json names the layers that make its project, in order,
from layers/ (a later layer's file replaces an earlier one's), plus any files of its
own. The runner copies them into a fresh git repo, runs `claude -p /ask-team` there with
read-only tools, and checks the answer:

    run       a regex the answer's last `Run:` line must match
    must      regexes the whole answer must match
    must_not  regexes it must not match

`_CLAUDE.md` in a layer becomes the project's CLAUDE.md; under its own name it would load
as instructions in sessions working on this repo.

The skill under test is the one Claude Code loads: ~/.claude/skills/ask-team, linked to
this repo's working tree. Each run is a full session on your account, so it costs money
and takes a minute or two; run it when the workflow changes, not on every commit.

    python3 tests/routing/run.py                    # every scenario, once
    python3 tests/routing/run.py sized-* --runs 3   # some scenarios, three times each
    python3 tests/routing/run.py --keep             # keep the projects, to look inside

Answers are saved in tests/routing/results/<time>/. Exit code 1 when any run fails.
"""
import argparse
import concurrent.futures
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.join(HERE, "layers")
SCENARIOS = os.path.join(HERE, "scenarios")
TOOLS = "Read,Glob,Grep,Bash(git log:*),Bash(git status:*),Bash(ls:*)"
GIT = {"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.com",
       "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.com",
       "GIT_AUTHOR_DATE": "2026-10-01T09:00:00", "GIT_COMMITTER_DATE": "2026-10-01T09:00:00"}


def build(scenario, where):
    for layer in scenario["layers"]:
        shutil.copytree(os.path.join(LAYERS, layer), where, dirs_exist_ok=True)
    for path, text in scenario.get("files", {}).items():
        os.makedirs(os.path.dirname(os.path.join(where, path)) or where, exist_ok=True)
        with open(os.path.join(where, path), "w", encoding="utf-8") as out:
            out.write(text)
    for root, _, files in os.walk(where):
        if "_CLAUDE.md" in files:
            os.replace(os.path.join(root, "_CLAUDE.md"), os.path.join(root, "CLAUDE.md"))
    env = {**os.environ, **GIT}
    for command in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                    ["git", "commit", "-q", "-m", "Fixture state"]):
        subprocess.run(command, cwd=where, env=env, check=True)


def grade(scenario, answer):
    """The reasons this answer fails the scenario; empty when it passes."""
    runs = re.findall(r"^\W*Run:\s*(.+?)\s*$", answer, re.M)
    if not runs:
        return ["no `Run:` line"]
    run = runs[-1].replace("`", "")
    failures = []
    if "run" in scenario and not re.search(scenario["run"], run):
        failures.append(f"Run line '{run}' does not match /{scenario['run']}/")
    failures += [f"answer lacks /{pattern}/" for pattern in scenario.get("must", [])
                 if not re.search(pattern, answer)]
    failures += [f"answer has /{pattern}/" for pattern in scenario.get("must_not", [])
                 if re.search(pattern, answer)]
    return failures


def run_once(name, scenario, number, results, args):
    where = tempfile.mkdtemp(prefix=f"routing-{name}-")
    try:
        build(scenario, where)
        command = ["claude", "-p", "/ask-team", "--output-format", "json", "--allowedTools", TOOLS,
                   "--disallowedTools", "Write,Edit,NotebookEdit", "--max-turns", "40"]
        if args.model:
            command += ["--model", args.model]
        done = subprocess.run(command, cwd=where, capture_output=True, text=True, timeout=900)
        try:
            output = json.loads(done.stdout)
        except json.JSONDecodeError:
            output = {"result": done.stdout + done.stderr, "total_cost_usd": 0}
        answer = output.get("result") or ""
        with open(os.path.join(results, f"{name}-{number}.md"), "w", encoding="utf-8") as out:
            out.write(answer)
        return name, number, grade(scenario, answer), output.get("total_cost_usd", 0), where
    finally:
        if not args.keep:
            shutil.rmtree(where, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("names", nargs="*", help="scenario names or globs (default: all)")
    parser.add_argument("--runs", type=int, default=1, help="runs per scenario")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="runs at once")
    parser.add_argument("--model", help="model for the runs (default: Claude Code's)")
    parser.add_argument("--keep", action="store_true", help="keep each run's project")
    args = parser.parse_args()

    scenarios = {}
    for file in sorted(os.listdir(SCENARIOS)):
        name = file.removesuffix(".json")
        if file.endswith(".json") and (not args.names or any(fnmatch.fnmatch(name, n) for n in args.names)):
            scenarios[name] = json.load(open(os.path.join(SCENARIOS, file), encoding="utf-8"))
    if not scenarios:
        sys.exit("no scenario matches")
    results = os.path.join(HERE, "results", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(results)

    outcomes, cost = {}, 0.0
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = [pool.submit(run_once, name, scenario, number, results, args)
                   for name, scenario in scenarios.items() for number in range(1, args.runs + 1)]
        for future in concurrent.futures.as_completed(futures):
            name, number, failures, run_cost, where = future.result()
            outcomes.setdefault(name, []).append((number, failures, where))
            cost += run_cost or 0

    failed = 0
    for name in scenarios:
        runs = sorted(outcomes[name])
        passed = sum(1 for _, failures, _ in runs if not failures)
        failed += len(runs) - passed
        print(f"{'PASS' if passed == len(runs) else 'FAIL'} {name}: {passed}/{len(runs)}")
        for number, failures, where in runs:
            for failure in failures:
                print(f"     run {number}: {failure}")
            if args.keep:
                print(f"     run {number}: project kept in {where}")
    print(f"answers in {os.path.relpath(results)}; cost ${cost:.2f}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
