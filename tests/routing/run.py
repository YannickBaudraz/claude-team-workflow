#!/usr/bin/env python3
"""Run /ask-team against fixture projects and check the command it answers.

Each scenario in scenarios/*.json names the layers that make its project, in order,
from layers/ (a later layer's file replaces an earlier one's), plus any files of its
own. The runner copies them into a fresh git repo, runs `claude -p /ask-team` there with
read-only tools, except writing in .claude/ask-team/, and checks the answer: that it has the
router's form (the state table, the Session, Gate, Next and After that parts), and what its
Next block holds. It also checks what the router saved: latest.md and a dated copy holding
the same answer, beside a .gitignore holding `*`, and nothing git can see. A scenario that
plants an old answer marks it with its `planted` string, and fails when that string comes back
in any tool result: read, listed or searched, the old answer reached the context.

A scenario with a `light` regex also runs as `/ask-team next`, the light answer: a few lines
and a Next block matching it (`^/ask-team$` when the light answer should hand over), and
nothing saved.

    ask       what the user brings, appended to /ask-team (default: nothing)
    next      a regex the answer's Next block must match
    must      regexes the whole answer must match
    must_not  regexes it must not match
    light     a regex the Next block of `/ask-team next` must match (default: not run light)
    saves     whether the router saves its answer here (default: true)
    git       whether the project is a git repo (default: true)

`_CLAUDE.md` in a layer becomes the project's CLAUDE.md; under its own name it would load
as instructions in sessions working on this repo.

The skill under test is the one Claude Code loads: ~/.claude/skills/ask-team, linked to
this repo's working tree. Each run is a full session on your account, so it costs money
and takes a minute or two; run it when the workflow changes, not on every commit.

    python3 tests/routing/run.py                    # every scenario, once
    python3 tests/routing/run.py sized-* --runs 3   # some scenarios, three times each
    python3 tests/routing/run.py --keep             # keep the projects, to look inside
    python3 tests/routing/run.py --model claude-opus-5-5 --effort medium
    python3 tests/routing/run.py --mode light       # only the light answers

Answers are saved in tests/routing/results/<time>/, with report.md: the commit and model
tested, and per scenario its fixture, what it expects, each run's verdict and full answer;
and summary.md: the same heading, then one line per scenario with each run's verdict and Next
block, small enough for a pull request comment.
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
TOOLS = ("Read,Glob,Grep,Bash(git log:*),Bash(git status:*),Bash(git worktree list:*),Bash(git rev-parse:*),"
         "Bash(ls:*),Bash(date:*),Write(./.claude/ask-team/**),Edit(./.claude/ask-team/**)")
GIT = {"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.com",
       "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.com",
       "GIT_AUTHOR_DATE": "2026-10-01T09:00:00", "GIT_COMMITTER_DATE": "2026-10-01T09:00:00"}

# The runner may itself be started from a Claude Code session: none of its variables (effort, session,
# socket) may reach the runs, or they would not run at the model and effort the report states.
CLEAN = {key: value for key, value in os.environ.items() if not re.match(r"(CLAUDE|ANTHROPIC)", key)}


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
    if not scenario.get("git", True):
        return
    env = {**os.environ, **GIT}
    # The user's global excludes may ignore CLAUDE.md or .claude: a fixture holds what its layers say.
    for command in (["git", "init", "-q", "-b", "main"], ["git", "-c", "core.excludesFile=/dev/null", "add", "-A"],
                    ["git", "commit", "-q", "-m", "Fixture state"]):
        subprocess.run(command, cwd=where, env=env, check=True)


def grade(scenario, answer):
    """The reasons this answer fails the scenario; empty when it passes."""
    if scenario.get("mode") == "light":
        lines = [line for line in answer.splitlines() if line.strip()]
        failures = [f"the light answer runs to {len(lines)} lines"] if len(lines) > 10 else []
    else:
        failures = [f"no {part}" for part, pattern in FORM.items() if not re.search(pattern, answer, re.M)]
    block = next_block(answer)
    if not block:
        return failures + ["no Next block"]
    if "next" in scenario and not re.search(scenario["next"], block):
        failures.append(f"Next block '{block}' does not match /{scenario['next']}/")
    failures += [f"answer lacks /{pattern}/" for pattern in scenario.get("must", [])
                 if not re.search(pattern, answer)]
    failures += [f"answer has /{pattern}/" for pattern in scenario.get("must_not", [])
                 if re.search(pattern, answer)]
    return failures


# The parts of the router's answer, as SKILL.md's Answer item lays them out.
FORM = {"state table": r"^\|\s*Step\s*\|\s*Home\s*\|\s*Found\s*\|\s*Approved\s*\|",
        "Session line": r"^\*\*Session:\*\*", "Gate line": r"^\*\*Gate:\*\*",
        "After that line": r"^\*\*After that:\*\*"}


def next_block(answer):
    """What the answer's last Next block holds, one line per option."""
    blocks = re.findall(r"^\*\*Next\*\*\s*\n+```[^\n]*\n(.*?)\n```", answer, re.M | re.S)
    return blocks[-1].strip() if blocks else ""


def saved(scenario, answer, where):
    """The reasons what the router saved, or left for git to see, fails the scenario."""
    folder = os.path.join(where, ".claude", "ask-team")
    failures = []
    if not scenario.get("saves", True):
        # What the scenario put there, if anything, stays as it was.
        given = {path: text for path, text in scenario.get("files", {}).items() if path.startswith(".claude/ask-team/")}
        found = {os.path.relpath(os.path.join(root, f), where): open(os.path.join(root, f), encoding="utf-8").read()
                 for root, _, files in os.walk(folder) for f in files}
        if found != given:
            failures.append("wrote in .claude/ask-team/, though this answer saves nothing")
    elif not os.path.exists(os.path.join(folder, "latest.md")):
        failures.append("no .claude/ask-team/latest.md")
    else:
        latest = open(os.path.join(folder, "latest.md"), encoding="utf-8").read()
        if next_block(latest) != next_block(answer):
            failures.append("latest.md does not hold the printed answer's Next block")
        if not [f for f in os.listdir(folder) if re.fullmatch(r"\d{4}-\d{2}-\d{2}-\d{4}-.+\.md", f)]:
            failures.append("no dated copy beside latest.md")
        ignore = os.path.join(folder, ".gitignore")
        if not os.path.exists(ignore) or open(ignore).read().strip() != "*":
            failures.append(".claude/ask-team/.gitignore does not hold *")
    if scenario.get("git", True):
        # Without the user's global excludes, which may already ignore .claude: only the
        # project's own rules and the folder's .gitignore count, as on any other machine.
        seen = subprocess.run(["git", "-c", "core.excludesFile=/dev/null", "status", "--porcelain",
                               "--untracked-files=all"], cwd=where,
                              capture_output=True, text=True).stdout.strip()
        if seen:
            failures.append("git sees: " + seen.replace("\n", ", "))
    return failures


def peeked(scenario, results_seen):
    """Whether a planted old answer, marked by the scenario's `planted` string in its content and
    file names, came back in any tool result: read, listed or searched, it reached the context."""
    marker = scenario.get("planted")
    if marker and any(marker in text for text in results_seen):
        return [f"an old saved answer reached the context: a tool result holds {marker}"]
    return []


def run_once(name, scenario, number, results, args):
    where = tempfile.mkdtemp(prefix=f"routing-{name}-")
    try:
        build(scenario, where)
        asked = "/ask-team next" if scenario.get("mode") == "light" else " ".join(["/ask-team", scenario.get("ask", "")]).strip()
        command = ["claude", "-p", asked, "--output-format", "stream-json", "--verbose",
                   "--allowedTools", TOOLS, "--disallowedTools", "NotebookEdit", "--max-turns", "40"]
        if args.model:
            command += ["--model", args.model]
        if args.effort:
            command += ["--effort", args.effort]
        done = subprocess.run(command, cwd=where, env=CLEAN, capture_output=True, text=True, timeout=900)
        output, seen = {"result": done.stdout[-2000:] + done.stderr[-2000:]}, []
        for line in done.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "user":
                content = event.get("message", {}).get("content", [])
                seen += [json.dumps(block.get("content", "")) for block in content
                         if isinstance(block, dict) and block.get("type") == "tool_result"]
            elif event.get("type") == "result":
                output = event
        answer = output.get("result") or ""
        with open(os.path.join(results, f"{name}-{number}.md"), "w", encoding="utf-8") as out:
            out.write(answer)
        failures = grade(scenario, answer) + saved(scenario, answer, where) + peeked(scenario, seen)
        return dict(name=name, number=number, failures=failures, answer=answer,
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


def pinned():
    """The model and effort the skill's frontmatter pins: they override the session's."""
    skill = open(os.path.expanduser("~/.claude/skills/ask-team/SKILL.md"), encoding="utf-8").read()
    front = re.match(r"---\n(.*?)\n---", skill, re.S).group(1)
    return {key: value.strip() for key, value in re.findall(r"^(model|effort):(.*)$", front, re.M)}


def claude_version():
    """The Claude Code version the runs used, as `claude --version` prints it, so a report names the version it ran on."""
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.split(" ")[0].strip() or "unknown"
    except OSError:
        return "unknown"


def heading(scenarios, outcomes, tested, effort):
    """The title and the line saying what was tested, shared by report.md and summary.md."""
    runs = [run for name in scenarios for run in outcomes[name]]
    models = sorted({model for run in runs for model in run["models"]})
    passed = sum(1 for run in runs if not run["failures"])
    return [f"# Routing scenarios: {passed}/{len(runs)} runs pass", "",
            f"Commit `{tested['sha'][:7]}`{' with local changes' if tested['dirty'] else ''}, "
            f"{time.strftime('%Y-%m-%d %H:%M')}, Claude Code {claude_version()}, model {', '.join(models) or 'unknown'}, "
            f"effort {pinned().get('effort') and pinned()['effort'] + ' (pinned by the skill)' or effort or 'from your settings'}, "
            f"cost ${sum(run['cost'] for run in runs):.2f}. Each run is `claude -p \"/ask-team [request]\"` "
            "in a fresh git repo built from the scenario's layers, with read-only tools; "
            "it passes when the answer has the router's form and its Next block matches.", ""]


def summary(scenarios, outcomes, tested, effort):
    """The compact proof, small enough for a pull request comment: each run's verdict and Next block."""
    most = max(len(runs) for runs in outcomes.values())
    lines = heading(scenarios, outcomes, tested, effort) + [
        "| Scenario | Expects Next to match | " + " | ".join(f"Run {n}" for n in range(1, most + 1)) + " |",
        "|---|---|" + "---|" * most]
    for name, scenario in scenarios.items():
        cells = []
        for run in outcomes[name]:
            shown = next_block(run["answer"]).replace(chr(10), " / ")
            shown = shown if len(shown) <= 60 else shown[:57] + "..."
            cells.append(("pass" if not run["failures"] else "**FAIL**") + (f" `{shown}`" if shown else ""))
        cells += [""] * (most - len(cells))
        lines.append(f"| {name} | `{scenario.get('next', '').replace('|', '\\|')}` | " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    return "\n".join(lines) + "\n"


def report(scenarios, outcomes, tested, effort):
    """The proof for a pull request: what was tested, and every run's answer."""
    lines = heading(scenarios, outcomes, tested, effort) + [
        "| Scenario | Expects Next to match | Runs passed |", "|---|---|---|"]
    for name, scenario in scenarios.items():
        ok = sum(1 for run in outcomes[name] if not run["failures"])
        lines.append(f"| [{name}](#{name}) | `{scenario.get('next', '').replace('|', '\\|')}` | {ok}/{len(outcomes[name])} |")
    for name, scenario in scenarios.items():
        ok = sum(1 for run in outcomes[name] if not run["failures"])
        layers = ", ".join(f"[{layer}]({tested['tree']}/layers/{layer})" for layer in scenario["layers"])
        lines += ["", f"## {name}", "", f"**{ok}/{len(outcomes[name])} pass.** {scenario['why']}", "",
                  f"- Project: layers {layers}" + (f", plus {', '.join(f'`{f}`' for f in scenario['files'])}"
                                                    if scenario.get("files") else ""),
                  f"- Asked: " + ("`/ask-team next`, the light answer" if scenario.get("mode") == "light"
                                  else scenario["ask"] if scenario.get("ask") else "plain `/ask-team`"),
                  f"- Expects: " + ("a light answer of a few lines" if scenario.get("mode") == "light" else "the router's form")
                  + f", and a Next block matching `{scenario.get('next', '')}`"
                  + "".join(f"; the answer matches `{m}`" for m in scenario.get("must", []))
                  + "".join(f"; the answer does not match `{m}`" for m in scenario.get("must_not", [])),
                  f"- Scenario file: [{name.removesuffix('-next')}.json]({tested['blob']}/scenarios/{name.removesuffix('-next')}.json)", "",
                  "| Run | Verdict | Next block |", "|---|---|---|"]
        for run in outcomes[name]:
            verdict = "pass" if not run["failures"] else "FAIL: " + "; ".join(run["failures"])
            lines.append(f"| {run['number']} | {verdict} | {next_block(run['answer']).replace('|', '\\|').replace(chr(10), ' / ')} |")
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
    parser.add_argument("--effort", help="effort for the runs (default: your settings for the model)")
    parser.add_argument("--mode", choices=("full", "light", "both"), default="both",
                        help="run /ask-team, /ask-team next, or both (default)")
    parser.add_argument("--keep", action="store_true", help="keep each run's project")
    args = parser.parse_args()

    scenarios = {}
    for file in sorted(os.listdir(SCENARIOS)):
        name = file.removesuffix(".json")
        if file.endswith(".json") and (not args.names or any(fnmatch.fnmatch(name, n) for n in args.names)):
            scenario = json.load(open(os.path.join(SCENARIOS, file), encoding="utf-8"))
            if args.mode != "light":
                scenarios[name] = scenario
            if args.mode != "full" and "light" in scenario:
                scenarios[f"{name}-next"] = {**{k: v for k, v in scenario.items() if k not in ("must", "must_not")},
                                             "mode": "light", "next": scenario["light"], "saves": False}
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
        out.write(report(scenarios, outcomes, tested, args.effort))
    with open(os.path.join(results, "summary.md"), "w", encoding="utf-8") as out:
        out.write(summary(scenarios, outcomes, tested, args.effort))
    cost = sum(run["cost"] for runs in outcomes.values() for run in runs)
    print(f"answers, report.md and summary.md in {os.path.relpath(results)}; cost ${cost:.2f}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
