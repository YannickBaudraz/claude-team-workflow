---
name: epic-retro
description: Run the retrospective of a finished epic from the evidence it left: sourced findings, a verdict against the epic's goals, and action items.
argument-hint: "<epic id>"
disable-model-invocation: true
---

# Epic retro

A retro closes each epic, as on a team using a Kanban flow. It reads the **evidence** the epic left, judges the result against what the epic set out to do, and proposes improvements. Every finding cites its source (a file and line, a commit, a pull request, a ticket, a review comment); a claim with no source is dropped.

## 1. Gather the evidence

Using the project map and the tracker doc (`docs/agents/issue-tracker.md`), collect:

- the epic, its PRD and design doc, its stories and tickets with their states;
- the merged pull requests, their review comments, and the commit range from the epic's first ticket to its last;
- the ADRs and glossary changes made during the epic;
- the previous epic's retro, if any, with its action items.

Record what is missing. Done when every ticket of the epic is accounted for and each gap in the evidence is written down.

## 2. Find what no single pull request shows

Look across the whole epic, especially at the boundaries between tickets where no session saw both sides:

- drift between the design doc, the ADRs and what was built;
- requirements of the PRD that no ticket delivered, or work no requirement asked for;
- duplication, growing modules, patterns that diverge between tickets;
- the process: rework, recurring review findings, tickets that stalled or were reopened;
- whether the previous retro's action items landed.

Done when each angle above has its findings with sources, or an explicit "nothing found".

## 3. Verdict

Judge the epic against its PRD's goals and its acceptance criteria: **accepted**, **accepted with open items**, or **not accepted**. An unfinished ticket makes it *not accepted* unless the user decides otherwise. The verdict is the user's to confirm.

## 4. Lessons

Call the Skill tool with `lesson-learned` on the epic's commit range, so the engineering lessons come from the code itself.

## 5. Action items and the document

Propose at most about 7 action items, each with an owner and where it lands: a rule in `CODING_STANDARDS.md`, a check a tool can run, a template change, or a ticket. Apply none of them; the user decides.

Write the retro where the project map puts retros: evidence gaps, findings with sources, verdict, lessons, action items, and the status of the previous retro's items.

Then tell the user the next step: `/retro` for improvements to the agents' environment from the epic's sessions.
