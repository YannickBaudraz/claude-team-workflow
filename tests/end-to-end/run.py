#!/usr/bin/env python3
"""Build and review one fixture ticket end to end, the way FLOW.md's steps 11 and 12 do.

The routing scenarios prove which command the router prints. This proves the commands it prints
work together: a ticket goes through `/build-ticket` in its own session, then `/acceptance-review`,
`/code-review-and-quality` and `/security-review` in one fresh review session, on the pantry project
with a ticket that touches a screen (the `screen` layer of tests/routing/layers). What it records is today's chain,
so a change to the chain shows up as a change here.

It runs before any change to the model, or to a skill of the build and review chain, reaches
main. Each changed step's own checks still run; other step skills need only their own fixtures.
A failed ticket is rerun once before looking for a cause, because one model run can fail by
chance. When several changes went in together and it still fails, they are tried one PR at a
time.

The project is a fresh git repo whose `origin` is a local bare repository, and gh is
tests/routing/stub/gh, so a run reaches no code host. The merge stays out: no step merges, and
the run fails if main moves. CI is run by this script on what was pushed, and its result is put
on the pull request as the `tests` check, before the reviews read it.

`/build-ticket` stops for the developer before the pull request; it stops before each commit only
when paired, and this run does not pair. A stand-in developer answers each stop with the same
fixed reply until the pull request is open and nothing is left to push, and each answer counts
as one of the developer's touches. The reply approves only what the session just showed: a
looser one would read as a blanket approval and undercount them. The skills' own Arguments
come from REGISTRY.md, as the router prints them.

The build takes the usual path, with no characterization test and no full-diff read for a small
change in an existing codebase: the fixture is a new product, its code and its setup one commit,
and its ticket belongs to a story. Its project map names GitHub Actions, but the fixture has no
pipeline files: this script stands in for that CI and runs the fixture's commands on what was
pushed, but not the test guards. The build runs the guards in its session and puts their lines
on the pull request, and nothing checks their reasons.

What passes: the chain reaches a pull request, CI on it is green, this script's own reading of
the page (page_check.py) finds every acceptance criterion met, no commit carries an attribution,
main has not moved, the acceptance review prints a verdict that agrees with page_check.py and posts
it on the pull request, and, unless that verdict stops the chain, the review is on the pull request
and the security review answers. The rest is recorded, not
judged: touches, the skills each session loaded, the documents it read, what the review asked
for, and what the page does beyond the ticket. Requested changes or a does-not-satisfy on a sound
build are the chain's answer, kept as found. A does-not-satisfy stops the chain there, as FLOW.md's
step 12 does, and the run never goes back to the build: rework is not part of it.

A run needs pytest, ruff and mypy on the machine, the fixture's own commands. Each session is a
full session on your account, so a run costs money and takes a while:

    python3 tests/end-to-end/run.py --model claude-opus-5-5 --effort medium
    python3 tests/end-to-end/run.py --keep              # keep the project, to look inside

Sessions, answers and report.md are saved in tests/end-to-end/results/<time>/. Exit code 1 when
the run fails.
"""
import argparse
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

# The page imports flow.py too, and must never run a stale cached copy of it (see build-workflow.py).
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [HERE, os.path.join(ROOT, "skills", "ask-team", "scripts")]

import flow
import page_check

spec = importlib.util.spec_from_file_location("routing_run", os.path.join(ROOT, "tests", "routing", "run.py"))
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)

TICKET = 5
PROJECT = {"layers": ["base", "code", "setup", "brief", "roadmap", "prd-approved", "design", "ui", "refined",
                      "ticketed", "screen"]}
TOOLS = ",".join(["Read", "Glob", "Grep", "Write", "Edit", "Agent", "Skill", "TodoWrite"] + [
    f"Bash({command}:*)" for command in (
        "git", "gh pr", "python3", "pytest", "ruff", "mypy", "ls", "cat", "head", "tail", "grep", "wc", "find", "mkdir",
        "date", "sleep", "curl", "kill", "pkill", "lsof", "sed", "awk", "sort", "echo", "pwd", "cd", "test", "true",
        "cp", "mktemp", "export", "set", "env", "timeout", "printf")])
REPLY = "Approved. If you are asking how to finish the branch: push and create a pull request."
MOST_REPLIES = 20
# What CI runs on every PR: the fixture's coding standards, by their commands.
CI = {"pytest": ["python3", "-m", "pytest", "-q"], "ruff check": ["ruff", "check", "src", "tests"],
      "ruff format": ["ruff", "format", "--check", "src", "tests"], "mypy": ["mypy", "src"]}
ATTRIBUTION = re.compile(r"co-authored-by|generated with|\bclaude\b|\bassistant\b", re.I)
SKILL_FILE = re.compile(r"skills/([\w-]+)/SKILL\.md\b(?!\.)")
VERDICT = re.compile(r"VERDICT:\s*(satisfies|does-not-satisfy|indeterminate)")
REVIEW = re.compile(r"\b(request(?:ing)? changes|changes (?:needed|required|requested)|approved?)\b", re.I)
# What a session may read, and how it would show in its Read paths or its commands.
DOCUMENTS = {"ticket": f"issues/{TICKET}-", "interface design": "docs/interface/", "design doc": "docs/design/",
             "PRD": "docs/prd/", "coding standards": "CODING_STANDARDS.md",
             "definition of done": "docs/definition-of-done.md"}


def printed(command, **values):
    """A step's command as the router prints it: with the Arguments of its REGISTRY.md row."""
    with open(os.path.join(ROOT, "skills", "ask-team", "REGISTRY.md"), encoding="utf-8") as registry:
        table = flow.workflow_tables(registry.read())[0]
    arguments = next(row["arguments"] for row in table if row["command"] == f"`{command}`").replace("`", "")
    for name, value in values.items():
        arguments = arguments.replace(f"<{name}>", str(value))
    return f"{command} {arguments}"


def read_session(lines):
    """What a session's stream-json says it did."""
    found = dict(answer="", id=None, cost=0, turns=0, error=None, skills=[], read=[], commands=[], denied=[])
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                given = block.get("input", {})
                if block.get("name") == "Skill":
                    found["skills"].append(given.get("skill", ""))
                elif block.get("name") == "Read":
                    found["read"].append(given.get("file_path", ""))
                    if given.get("file_path", "").endswith("/SKILL.md"):
                        found["skills"].append(given["file_path"].split("/")[-2])
                elif block.get("name") == "Bash":
                    found["commands"].append(given.get("command", ""))
                    # A skill read with cat or head is read all the same.
                    found["skills"] += SKILL_FILE.findall(given.get("command", ""))
        elif event.get("type") == "result":
            found.update(answer=event.get("result") or "", id=event.get("session_id"), turns=event.get("num_turns") or 0,
                         cost=event.get("total_cost_usd") or 0, denied=event.get("permission_denials") or [],
                         error=event.get("subtype") if event.get("is_error") else None)
    return found


def add(total, part):
    """A session's facts added to its step's, for a build that runs over several replies."""
    for key in ("cost", "turns"):
        total[key] += part[key]
    for key in ("skills", "read", "commands", "denied"):
        total[key] += part[key]
    total.update(answer=part["answer"], error=part["error"], id=part["id"] or total["id"])
    return total


def session(name, prompt, where, args, results, resume=None):
    command = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--allowedTools", TOOLS,
               "--disallowedTools", "NotebookEdit", "--max-turns", "120", "--max-budget-usd", str(args.budget)]
    command += ["--resume", resume] if resume else []
    command += ["--model", args.model] if args.model else []
    command += ["--effort", args.effort] if args.effort else []
    try:
        done = subprocess.run(command, cwd=where, env=args.env, capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired as expired:
        return dict(read_session([]), error=f"no answer after {expired.timeout} seconds")
    with open(os.path.join(results, f"{name}.jsonl"), "a", encoding="utf-8") as out:
        out.write(done.stdout)
    found = read_session(done.stdout.splitlines())
    if found["id"] is None:
        found["error"] = (done.stderr or done.stdout)[-500:] or "no result"
    return found


def open_prs(where):
    with open(os.path.join(where, ".git", "fixture-prs.json"), encoding="utf-8") as state:
        return [pr for pr in json.load(state) if pr.get("state", "OPEN") == "OPEN"]


def finished(where):
    """Whether the build has left nothing behind: its pull request is open and all of it is pushed."""
    listed = open_prs(where)
    if not listed:
        return False
    git = lambda *a: subprocess.run(["git", *a], cwd=where, capture_output=True, text=True).stdout.strip()
    return not git("status", "--porcelain", "--untracked-files=no") and git(
        "rev-list", "--count", f"origin/{listed[0]['headRefName']}..HEAD") == "0"


def build_project(where, env):
    """The fixture, pushed to a local bare repository as its origin, with an empty store."""
    routing.build(PROJECT, where)
    origin = where + ".origin.git"
    for command in (["git", "init", "-q", "--bare", "-b", "main", origin], ["git", "remote", "add", "origin", origin],
                    ["git", "push", "-q", "origin", "main"], ["git", "fetch", "-q", "origin"],
                    ["git", "remote", "set-head", "origin", "main"]):
        subprocess.run(command, cwd=where, env=env, check=True)
    return subprocess.run(["git", "rev-parse", "main"], cwd=where, capture_output=True, text=True, check=True).stdout.strip()


def pushed_copy(where, sha):
    """What was pushed, in a clean folder: what CI and the page check see."""
    copy = tempfile.mkdtemp(prefix="end-to-end-head-")
    archive = subprocess.run(["git", "archive", sha], cwd=where, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(copy, filter="data")
    return copy


def run_ci(copy, env):
    return {name: subprocess.run(command, cwd=copy, env=env, capture_output=True, text=True).returncode == 0
            for name, command in CI.items()}


def put_check(where, ci):
    """The `tests` check on the pull request, as CI would report it."""
    path = os.path.join(where, ".git", "fixture-prs.json")
    with open(path, encoding="utf-8") as state:
        listed = json.load(state)
    for pr in listed:
        pr["statusCheckRollup"] = [{"name": "tests", "status": "COMPLETED",
                                    "conclusion": "SUCCESS" if all(ci.values()) else "FAILURE"}]
    with open(path, "w", encoding="utf-8") as state:
        json.dump(listed, state)


def ticket_status(text):
    match = re.search(r"^Status:\s*(.+)$", text, re.M)
    return match.group(1).strip() if match else None


def ticket_file(root):
    folder = os.path.join(root, "issues")
    name = next(f for f in os.listdir(folder) if f.startswith(f"{TICKET}-"))
    with open(os.path.join(folder, name), encoding="utf-8") as ticket:
        return ticket.read()


def review_word(text):
    """What a posted review says: its first request for changes or approval."""
    match = REVIEW.search(text)
    return match.group(1).lower() if match else None


def documents_read(found):
    text = "\n".join(found["read"] + found["commands"])
    return [name for name, path in DOCUMENTS.items() if path in text]


def build_step(where, args, results, facts):
    found = session("build", f"/build-ticket {TICKET}", where, args, results)
    total = dict(found)
    facts["replies"] = 0
    while not found["error"] and not finished(where) and facts["replies"] < MOST_REPLIES:
        facts["replies"] += 1
        found = session("build", REPLY, where, args, results, resume=total["id"])
        total = add(total, found)
    facts["steps"]["build"] = total
    facts["finished"] = finished(where)
    listed = open_prs(where)
    if not listed:
        return None
    pr = listed[0]
    sha = subprocess.run(["git", "rev-parse", f"origin/{pr['headRefName']}"], cwd=where, capture_output=True, text=True, check=True).stdout.strip()
    log = subprocess.run(["git", "log", "--format=%H%x00%s%x00%b%x01", f"origin/main..{sha}"], cwd=where,
                         capture_output=True, text=True, check=True).stdout
    commits = [entry.strip().split("\0") for entry in log.split("\x01") if entry.strip()]
    facts.update(number=pr.get("number"), branch=pr["headRefName"], body=pr.get("body", ""), sha=sha,
                 **{"body attributed": bool(ATTRIBUTION.search(pr.get("body", "")))},
                 commits=[commit[1] for commit in reversed(commits)],
                 attributed=[commit[1] for commit in commits if ATTRIBUTION.search(" ".join(commit[1:]))])
    copy = pushed_copy(where, sha)
    try:
        facts["ci"] = run_ci(copy, args.env)
        put_check(where, facts["ci"])
        facts["page"] = page_check.check(copy, args.env["PANTRY_STORE"])
        facts["status pushed"] = ticket_status(ticket_file(copy))
    finally:
        shutil.rmtree(copy, ignore_errors=True)
    facts["status in the folder"] = ticket_status(ticket_file(where))
    return pr


def posts(where):
    state = open_prs(where)[0]
    return [post.get("body", "") for post in state.get("comments", []) + state.get("reviews", [])]


def review_steps(where, args, results, facts, pr):
    """FLOW.md's step 12, in one fresh session: the acceptance review first, then the code review and the
    security review, unless the acceptance verdict stops the chain."""
    number = pr["number"]
    accept = session("acceptance-review", printed("/acceptance-review", PR=number, ticket=TICKET), where, args, results)
    facts["steps"]["acceptance review"] = accept
    verdict = VERDICT.search(accept["answer"])
    facts["verdict"] = verdict.group(1) if verdict else None
    before = posts(where)
    facts["verdict posted"] = any(VERDICT.match(post.strip()) for post in before)
    if facts["verdict"] == "does-not-satisfy" or accept["id"] is None:
        return
    facts["steps"]["code review"] = session(
        "code-review", printed("/code-review-and-quality", PR=number), where, args, results, resume=accept["id"])
    # The developer's own command in FLOW.md's step 12: the security review reads the current branch.
    checkout = subprocess.run(["gh", "pr", "checkout", str(number), "--detach"], cwd=where, env=args.env, capture_output=True, text=True)
    facts["checkout"] = checkout.returncode == 0 or checkout.stderr.strip()
    facts["steps"]["security review"] = session(
        "security-review", "/security-review", where, args, results, resume=accept["id"])
    after = posts(where)[len(before):]
    facts["posted"] = len(after)
    facts["review says"] = review_word("\n".join(after))


def judge(facts):
    """The reasons this run fails; empty when it passes."""
    failures = [f"{name}: {step['error']}" for name, step in facts["steps"].items() if step.get("error")]
    if facts.get("number") is None:
        return failures + [f"the build opened no pull request after {facts.get('replies', 0)} replies"]
    if not facts["finished"]:
        failures.append(f"the build left work unpushed after {facts['replies']} replies")
    failures += [f"CI failed: {name}" for name, ok in facts["ci"].items() if not ok]
    failures += [f"the page fails the ticket: {name}" for name, ok in facts["page"]["contract"].items() if not ok]
    failures += [f"a commit carries an attribution: {subject}" for subject in facts["attributed"]]
    if facts.get("main moved"):
        failures.append("main moved: no step may merge")
    if not re.match(rf"{TICKET}\b", facts["branch"]):
        failures.append(f"branch {facts['branch']} is not named after the ticket")
    if not re.search(rf"#{TICKET}\b", facts["body"]):
        failures.append("the pull request does not link its ticket")
    if "in review" not in (facts.get("status pushed"), facts.get("status in the folder")):
        failures.append("the ticket did not move to in review")
    if "acceptance review" not in facts["steps"]:
        return failures + ["the reviews did not run"]
    sound = not any(not ok for ok in facts["page"]["contract"].values()) and all(facts["ci"].values())
    if facts.get("verdict") is None:
        failures.append("the acceptance review printed no verdict")
    elif facts["verdict"] == "satisfies" and not sound:
        failures.append("the acceptance review passed a ticket that fails its own check")
    if facts.get("verdict") and not facts.get("verdict posted"):
        failures.append("the acceptance review did not post its verdict on the pull request")
    if facts.get("verdict") == "does-not-satisfy":
        if "code review" in facts["steps"]:
            failures.append("the chain went on after a does-not-satisfy")
        return failures
    if "code review" not in facts["steps"]:
        return failures + ["the code and security reviews did not run"]
    if not facts.get("posted"):
        failures.append("the code review posted nothing on the pull request")
    if facts.get("checkout") is not True:
        failures.append(f"gh pr checkout failed: {facts.get('checkout')}")
    if not facts["steps"]["security review"]["answer"].strip():
        failures.append("the security review gave no answer")
    return failures


def report(facts, failures, tested, args, minutes, path):
    steps = facts["steps"]
    cost = sum(step["cost"] for step in steps.values())
    lines = [f"# End-to-end ticket: {'passed' if not failures else 'FAILED'}", "",
             f"Commit `{tested['sha'][:7]}`{' with local changes' if tested['dirty'] else ''}, {time.strftime('%Y-%m-%d %H:%M')}, "
             f"Claude Code {routing.claude_version()}, model {args.model or 'from your settings'}, "
             f"effort {args.effort or 'from your settings'}, {minutes:.0f} minutes, cost ${cost:.2f}.", ""]
    lines += [f"- FAIL: {failure}" for failure in failures] + ([""] if failures else [])
    lines += [f"Ticket #{TICKET}, branch `{facts.get('branch')}`, pull request #{facts.get('number')}. "
              f"Developer's touches in the build: {facts.get('replies', 0)}. "
              f"Acceptance verdict: `{facts.get('verdict')}`. Posts on the pull request: {facts.get('posted', 0)}, "
              f"saying `{facts.get('review says')}`. An attribution in the pull request's body: "
              f"{'yes' if facts.get('body attributed') else 'no'}.", "",
              "| Step | Turns | Skills loaded | Documents read | Tools refused |", "|---|---|---|---|---|"]
    for name, step in steps.items():
        skills = ", ".join(sorted(set(step["skills"]))) or "none"
        lines.append(f"| {name} | {step['turns']} | {skills} | "
                     f"{', '.join(documents_read(step)) or 'none'} | {len(step['denied'])} |")
    refused = [(name, denial) for name, step in steps.items() for denial in step["denied"]]
    if refused:
        lines += ["", "Tools refused:", ""]
        lines += [f"- {name}: `{json.dumps(denial.get('tool_input', {}))[:160]}`" for name, denial in refused]
    if "ci" in facts:
        lines += ["", "| CI on what was pushed | |", "|---|---|"]
        lines += [f"| {name} | {'pass' if ok else 'FAIL'} |" for name, ok in facts["ci"].items()]
        lines += ["", "| The page, read by this script | |", "|---|---|"]
        lines += [f"| ticket: {name} | {'pass' if ok else 'FAIL'} |" for name, ok in facts["page"]["contract"].items()]
        lines += [f"| design, recorded only: {name} | {'yes' if ok else 'no'} |" for name, ok in facts["page"]["design"].items()]
        lines += [f"| recorded only: escapes an item's name | {'yes' if facts['page']['escapes'] else 'no'} |",
                  f"| recorded only: answers beside an idle connection | {'yes' if facts['page']['idle'] else 'no'} |"]
        lines += ["", "Commits: " + "; ".join(f"`{subject}`" for subject in facts["commits"]) + "."]
    for name, step in steps.items():
        lines += ["", f"<details><summary>{name}: its last answer</summary>", "", step["answer"].strip(), "", "</details>"]
    with open(path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", help="model for the sessions (default: Claude Code's)")
    parser.add_argument("--effort", help="effort for the sessions (default: your settings for the model)")
    parser.add_argument("--budget", type=float, default=15, help="the most one session may spend, in dollars")
    parser.add_argument("--keep", action="store_true", help="keep the project, to look inside")
    args = parser.parse_args()

    results = os.path.join(HERE, "results", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(results)
    where = tempfile.mkdtemp(prefix="end-to-end-")
    args.env = {**routing.CLEAN, "PANTRY_STORE": where + ".store.json"}
    facts = {"steps": {}}
    tested, started = routing.commit(), time.time()
    try:
        base = build_project(where, {**os.environ, **routing.GIT})
        pr = build_step(where, args, results, facts)
        if pr:
            review_steps(where, args, results, facts, pr)
        for ref in ("main", "origin/main"):
            moved = subprocess.run(["git", "rev-parse", ref], cwd=where, capture_output=True, text=True).stdout.strip() != base
            facts["main moved"] = facts.get("main moved") or moved
        failures = judge(facts)
        path = os.path.join(results, "report.md")
        report(facts, failures, tested, args, (time.time() - started) / 60, path)
    finally:
        if not args.keep:
            for path_left in (where, where + ".origin.git"):
                shutil.rmtree(path_left, ignore_errors=True)
            if os.path.exists(args.env["PANTRY_STORE"]):
                os.unlink(args.env["PANTRY_STORE"])
    print(f"{'PASS' if not failures else 'FAIL'}: cost ${sum(s['cost'] for s in facts['steps'].values()):.2f}, report in {os.path.relpath(path)}")
    for failure in failures:
        print(f"  {failure}")
    if args.keep:
        print(f"  project kept in {where}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
