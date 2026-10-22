#!/usr/bin/env python3
"""Run /ask-team against fixture projects and check the command it answers.

Each scenario in scenarios/*.json names the layers that make its project, in order,
from layers/ (a later layer's file replaces an earlier one's), plus any files of its
own. The runner copies them into a fresh git repo, runs `claude -p /ask-team` there with
read-only tools, and checks the answer:

    ask       what the user brings, appended to /ask-team (default: nothing)
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

Answers are saved in tests/routing/results/<time>/, with report.md: the commit and model
tested, and per scenario its fixture, what it expects, each run's verdict and full answer.
Post it on the pull request as the proof. Exit code 1 when any run fails.
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
    run = last_run_line(answer)
    if not run:
        return ["no `Run:` line"]
    failures = []
    if "run" in scenario and not re.search(scenario["run"], run):
        failures.append(f"Run line '{run}' does not match /{scenario['run']}/")
    failures += [f"answer lacks /{pattern}/" for pattern in scenario.get("must", [])
                 if not re.search(pattern, answer)]
    failures += [f"answer has /{pattern}/" for pattern in scenario.get("must_not", [])
                 if re.search(pattern, answer)]
    return failures


def last_run_line(answer):
    runs = re.findall(r"^\W*Run:\s*(.+?)\s*$", answer, re.M)
    return runs[-1].replace("`", "") if runs else ""


def run_once(name, scenario, number, results, args):
    where = tempfile.mkdtemp(prefix=f"routing-{name}-")
    try:
        build(scenario, where)
        command = ["claude", "-p", " ".join(["/ask-team", scenario.get("ask", "")]).strip(), "--output-format", "json", "--allowedTools", TOOLS,
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
        return dict(name=name, number=number, failures=grade(scenario, answer), answer=answer,
                    cost=output.get("total_cost_usd") or 0, models=sorted(output.get("modelUsage", {})),
                    where=where)
    finally:
        if not args.keep:
            shutil.rmtree(where, ignore_errors=True)


def commit():
    """The commit under test, its GitHub tree URL, and whether tracked files differ from it."""
    git = lambda *a: subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True).stdout.strip()
    sha = git("rev-parse", "HEAD")
    remote = re.sub(r"\.git$", "", re.sub(r"^git@github\.com:", "https://github.com/", git("remote", "get-url", "origin")))
    return dict(sha=sha, tree=f"{remote}/tree/{sha}/tests/routing", blob=f"{remote}/blob/{sha}/tests/routing",
                dirty=bool(git("status", "--porcelain", "--untracked-files=no")))


def report(scenarios, outcomes, tested):
    """The proof for a pull request: what was tested, and every run's answer."""
    runs = [run for name in scenarios for run in outcomes[name]]
    models = sorted({model for run in runs for model in run["models"]})
    passed = sum(1 for run in runs if not run["failures"])
    lines = [f"# Routing scenarios: {passed}/{len(runs)} runs pass", "",
             f"Commit `{tested['sha'][:7]}`{' with local changes' if tested['dirty'] else ''}, "
             f"{time.strftime('%Y-%m-%d %H:%M')}, model {', '.join(models) or 'unknown'}, "
             f"cost ${sum(run['cost'] for run in runs):.2f}. Each run is `claude -p \"/ask-team [request]\"` "
             "in a fresh git repo built from the scenario's layers, with read-only tools; "
             "it passes when the answer's last `Run:` line matches.", "",
             "| Scenario | Expects `Run:` to match | Runs passed |", "|---|---|---|"]
    for name, scenario in scenarios.items():
        ok = sum(1 for run in outcomes[name] if not run["failures"])
        lines.append(f"| [{name}](#{name}) | `{scenario.get('run', '')}` | {ok}/{len(outcomes[name])} |")
    for name, scenario in scenarios.items():
        ok = sum(1 for run in outcomes[name] if not run["failures"])
        layers = ", ".join(f"[{layer}]({tested['tree']}/layers/{layer})" for layer in scenario["layers"])
        lines += ["", f"## {name}", "", f"**{ok}/{len(outcomes[name])} pass.** {scenario['why']}", "",
                  f"- Project: layers {layers}" + (f", plus {', '.join(f'`{f}`' for f in scenario['files'])}"
                                                    if scenario.get("files") else ""),
                  f"- Request: {scenario['ask'] if scenario.get('ask') else 'none, plain `/ask-team`'}",
                  f"- Expects: `Run:` matches `{scenario.get('run', '')}`"
                  + "".join(f"; the answer matches `{m}`" for m in scenario.get("must", []))
                  + "".join(f"; the answer does not match `{m}`" for m in scenario.get("must_not", [])),
                  f"- Scenario file: [{name}.json]({tested['blob']}/scenarios/{name}.json)", "",
                  "| Run | Verdict | `Run:` line |", "|---|---|---|"]
        for run in outcomes[name]:
            verdict = "pass" if not run["failures"] else "FAIL: " + "; ".join(run["failures"])
            lines.append(f"| {run['number']} | {verdict} | {last_run_line(run['answer']).replace('|', '\\|')} |")
        for run in outcomes[name]:
            lines += ["", f"<details><summary>Run {run['number']}: the router's full answer</summary>", "",
                      run["answer"].strip(), "", "</details>"]
    return "\n".join(lines) + "\n"


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

    tested = commit()
    outcomes = {}
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
        futures = [pool.submit(run_once, name, scenario, number, results, args)
                   for name, scenario in scenarios.items() for number in range(1, args.runs + 1)]
        for future in concurrent.futures.as_completed(futures):
            outcome = future.result()
            outcomes.setdefault(outcome["name"], []).append(outcome)
    for runs in outcomes.values():
        runs.sort(key=lambda run: run["number"])

    failed = 0
    for name in scenarios:
        runs = outcomes[name]
        passed = sum(1 for run in runs if not run["failures"])
        failed += len(runs) - passed
        print(f"{'PASS' if passed == len(runs) else 'FAIL'} {name}: {passed}/{len(runs)}")
        for run in runs:
            for failure in run["failures"]:
                print(f"     run {run['number']}: {failure}")
            if args.keep:
                print(f"     run {run['number']}: project kept in {run['where']}")
    with open(os.path.join(results, "report.md"), "w", encoding="utf-8") as out:
        out.write(report(scenarios, outcomes, tested))
    cost = sum(run["cost"] for runs in outcomes.values() for run in runs)
    print(f"answers and report.md in {os.path.relpath(results)}; cost ${cost:.2f}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
