#!/usr/bin/env python3
"""Check that the workflow's hand-offs close: FLOW.md's step contracts against the
registry, the project map template and this repo's skills.

- Every step of the main flow has a contract, and every contract row a step or a way in.
- Every need is made by an earlier step or by a way in, unless it comes from outside.
- Every output has a maker and a home, and every maker says it makes it: its Does line
  names the output, or a sentence of its Arguments creates, writes or saves it. A skill of
  this repo says it in its own SKILL.md.
- Every home is a kind of document the project map template places, a tool of its Tools table,
  or a path. Its other tables, such as the project's facts, name no homes.
- Every document a gated step makes has a maker that writes its approval line, the
  `Approved by <name> on <date>` FLOW.md defines, in its Arguments or its own SKILL.md.
- Every command this repo's workflow skills name is in the registry.

Reads only files in this repo, so CI can run it. Exit code 1 when anything is wrong.
"""
import os
import re
import sys

# The page imports flow.py too, and must never run a stale cached copy of it (see build-workflow.py).
sys.dont_write_bytecode = True

import flow

HERE = os.path.dirname(os.path.realpath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))
FLOW = os.path.join(SKILLS, "ask-team", "FLOW.md")
REGISTRY = os.path.join(SKILLS, "ask-team", "REGISTRY.md")
MAP = os.path.join(SKILLS, "ask-team", "templates", "project-map.md")
# The files of this repo's workflow skills whose commands must be in the registry.
WORKFLOW_FILES = ["ask-team/SKILL.md", "ask-team/ROUTER.md", "ask-team/FLOW.md", "build-ticket/SKILL.md",
                  "change-request/SKILL.md", "epic-retro/SKILL.md", "project-setup/SKILL.md"]
# A sentence that hands a skill an output to make: "Save where the map puts the PRD".
MAKING = re.compile(r"\b(creat|writ|sav|publish|post|mark|record|open)\w*", re.I)


def stem(word):
    word = word.lower()
    return word[:-1] if word.endswith("s") and not word.endswith("ss") else word


def says_it_makes(text, output, sentences_only):
    """Whether text names output's head noun: anywhere, or in a sentence that makes it."""
    noun = stem(output.split()[-1])
    pattern = re.compile(rf"\b{re.escape(noun)}", re.I)
    if not sentences_only:
        return bool(pattern.search(text))
    return any(pattern.search(s) and MAKING.search(s) for s in re.split(r"(?<=[.;])\s+", text))


problems = []
router = open(FLOW, encoding="utf-8").read()

# A row with no output cell is no step, so the contracts report it as missing.
flow_rows = [(number, cells) for number, cells in flow.main_flow(router) if len(cells) > 1]
steps = [number for number, _ in flow_rows]
# A gated step's output is approved, as the page reads it too; the merge is step 13's own gate.
gated = {number for number, cells in flow_rows if flow.approved(cells[-1])}
# Homes that hold tracker items or pull requests: approved by being published or merged.
NOT_DOCUMENTS = {"Issue tracker", "Epics, stories and tickets", "Code host"}
contracts = flow.step_contracts(router)
if contracts is None:
    sys.exit("PROBLEM FLOW.md: Step contracts should hold two tables, the steps and the outputs")
step_rows, output_rows = contracts

registry = {row["command"].strip("`"): row
            for table in flow.workflow_tables(open(REGISTRY, encoding="utf-8").read()) for row in table}

kinds = flow.map_homes(open(MAP, encoding="utf-8").read())

# The steps: what each needs and makes, in flow order; a way in is keyed by its command.
made_at, needs = {}, {}
for key, need, make in step_rows:
    if not isinstance(key, int) and key not in registry:
        problems.append(f"Step contracts: way in {key} is not in the registry")
    needs[key] = need
    for output in make:
        made_at.setdefault(output, []).append(key)
contracted = sorted(k for k in needs if isinstance(k, int))
if contracted != steps:
    problems.append(f"Step contracts cover steps {contracted}, the main flow has {steps}")

outputs = {}
for output, makers, home in output_rows:
    outputs[output] = home
    if output not in made_at:
        problems.append(f"Step contracts: {output} has a maker but no step makes it")
    for maker in makers:
        if maker == "the user":
            continue
        row = registry.get(maker)
        if row is None:
            problems.append(f"Step contracts: {output} is made by {maker}, which is not in the registry")
            continue
        # The maker's step, from its Used at, or the way in it is: that step lists the output.
        at = flow.used_at(row)[0]
        at = maker if at is None and maker in needs else at
        if at is not None and at not in made_at.get(output, []):
            problems.append(f"Step contracts: {maker} makes {output}, but its step {at} does not list it")
        own = os.path.join(SKILLS, maker.lstrip("/"), "SKILL.md")
        if row["source"].strip("`") == "YannickBaudraz/claude-team-workflow" and os.path.exists(own):
            said = says_it_makes(open(own, encoding="utf-8").read(), output, sentences_only=False)
        else:
            said = (says_it_makes(row.get("does", ""), output, sentences_only=False)
                    or says_it_makes(row.get("arguments", ""), output, sentences_only=True))
        if not said:
            problems.append(f"Step contracts: {maker} makes {output}, but neither its Does line "
                            f"nor its Arguments say so")
    if not (home in kinds or re.fullmatch(r"`[^`]+`", home)):
        problems.append(f"Step contracts: {output} lives in '{home}', which is not a row of the project map")
for output, home in outputs.items():
    if home in NOT_DOCUMENTS:
        continue
    for step in (at for at in made_at.get(output, []) if at in gated):
        makers = next(row[1] for row in output_rows if row[0] == output)
        writers = [m for m in makers if flow.used_at(registry.get(m, {}))[0] == step]
        for maker in writers:
            row = registry[maker]
            own = os.path.join(SKILLS, maker.lstrip("/"), "SKILL.md")
            text = (open(own, encoding="utf-8").read() if row["source"].strip("`") == "YannickBaudraz/claude-team-workflow"
                    and os.path.exists(own) else row.get("arguments", ""))
            if "Approved by" not in text:
                problems.append(f"Step contracts: step {step} is gated, but {maker} never writes the approval line on the {output}")
for output in made_at:
    if output not in outputs:
        problems.append(f"Step contracts: {output} is made but has no row saying who makes it and where it lives")

for key, groups in needs.items():
    for group in groups:
        if any(alt.endswith("(outside)") for alt in group):
            continue
        for alt in group:
            if alt not in made_at:
                problems.append(f"Step contracts: step {key} needs {alt}, which nothing makes")
        # A step needs one of the alternatives made before it, or by a way in.
        if isinstance(key, int) and not any(
                any(not isinstance(at, int) or at < key for at in made_at.get(alt, [])) for alt in group):
            problems.append(f"Step contracts: step {key} needs {' or '.join(group)}, made by no earlier step or way in")

for name in WORKFLOW_FILES:
    text = open(os.path.join(SKILLS, name), encoding="utf-8").read()
    for command in sorted(set(re.findall(r"`(/[a-z][a-z0-9:-]*)", text))):
        if command not in registry and command.lstrip("/") not in registry:
            problems.append(f"{name} names {command}, which is not in the registry")

print(f"{len(steps)} steps and {len(outputs)} outputs checked")
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
