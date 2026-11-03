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

- the epic, its PRD, its interface design when it has one, and its design doc, its stories and tickets with their states;
- the merged pull requests, their review comments, and the commit range from the epic's first ticket to its last;
- the ADRs and glossary changes made during the epic;
- the previous epic's retro, if any, with its action items.

Record what is missing. Done when every ticket of the epic is accounted for and each gap in the evidence is written down.

## 2. Find what no single pull request shows

Look across the whole epic, especially at the boundaries between tickets where no session saw both sides:

- drift between the design doc, the interface design, the product's visual direction, the ADRs and what was built;
- requirements of the PRD that no ticket delivered, or work no requirement asked for;
- duplication, growing modules, patterns that diverge between tickets;
- the process: rework, recurring review findings, tickets that stalled or were reopened;
- whether the previous retro's action items landed.

Done when each angle above has its findings with sources, or an explicit "nothing found".

## 3. Verdict

Judge the epic against its PRD's goals and its acceptance criteria: **accepted**, **accepted with open items**, or **not accepted**. An unfinished ticket makes it *not accepted* unless the user decides otherwise. The verdict is the user's to confirm. When the project map's kind is client, the client's decision on the epic counts too: record it in writing, through the documentation tool's approval feature or an email or ticket kept as evidence, and link it in the retro beside the user's confirmation. Once both are in, close the epic on the tracker, and its parent issue too when this epic was the last one open under it.

## 4. Confirm the project facts

Go through the project map's Project facts table with the user, the kind included: does each fact still hold? A tool may have gained users or a deploy target, or a personal project may have become a client's. Write each value the user confirms or changes, with today's date. A fact that changed sends the work it turns on through `/change-request`: name that work among the action items, with `/change-request <what the changed fact turns on>` as its next command. When the map has no Project facts table yet, propose its rows from the template and the epic's evidence, and add them once the user confirms.

Done when every fact carries today's date.

## 5. Lessons

Call the Skill tool with `lesson-learned` on the epic's commit range, so the engineering lessons come from the code itself.

## 6. Action items and the document

Propose at most about 7 action items, each with an owner and where it lands: a rule in the coding standards the project map names, a check a tool can run, a template change, or a ticket. Apply none of them; the user decides.

Write the retro where the project map puts retros: evidence gaps, findings with sources, verdict, lessons, action items, and the status of the previous retro's items.

Then tell the user the next step: `/retro` for improvements to the agents' environment from the epic's sessions.
