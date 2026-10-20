---
name: ask-team
description: Ask which skill to run next in a project worked the way an engineering team works, from discovery to retro. A router over the team workflow's skills.
disable-model-invocation: true
---

# Ask team

The project is worked the way a real engineering team works: discovery, roadmap, epics, refinement, tickets, test-first build, peer review, approval, retro. This skill tells the user which command to run next, with what arguments, in which session. It never runs the step itself: it **prints the next command**, ready to paste.

Before naming any skill, look it up in [REGISTRY.md](REGISTRY.md): its exact command, whether Claude may load it on its own, what it calls, and the arguments that redirect it to this workflow's conventions. A skill missing from the registry is not part of the workflow.

## How to route

1. **Read the state.** Find the project map (the project's `CLAUDE.md` or `AGENTS.md` points to it). No map yet: the project is before setup. With a map, read the tracker doc it names and check what exists and what is approved: the problem statement and brief, the roadmap, each epic's design doc and PRD, its stories, tickets, open PRs, and retros, and the sized issues whose next step has not started. The **frontier** is the first step whose input exists and whose output does not. When the map's Roadmap row says the roadmap is planned at step 4 only when wanted, steps 4 and 5 are not a frontier: with nothing in flight, offer `/change-request` for a change, or step 4 to plan the product.
2. **Size the request.** A change to an existing project that is not sized yet goes to `/change-request <change>` first: it diagnoses or grills the change as needed, sizes it with the user and writes it as one issue for the next session to start from; this router only reads those issues. A *spike* (one question to answer) goes to `prototype` or `research`; its answer goes on the request's issue when it has one, and the request is sized again. A *bounded* change (one ticket's worth) goes straight to the ticket path: write the ticket, then build it. An *architectural* change, or a new product, takes the main flow. Teams don't write a PRD for a typo.
3. **Answer** with: the step and why it is next, the exact command with its arguments, which session to run it in (see Sessions), and what has to be approved before the step after it. Done when the user can paste the command and knows where.

## Main flow

| # | Step | Command | Output, and the gate before moving on |
|---|---|---|---|
| 1 | Discovery | `/grill-with-docs <idea>` (before any project folder exists: `/grill-me`) | Shared understanding; glossary terms and ADRs in the repo. Reads the domain doc first when one exists. |
| 2 | Setup | `/project-setup`, then `/setup-matt-pocock-skills` | Project map, tracker doc, conventions. |
| 3 | Fog (only when the way is unclear) | `/wayfinder` | Decisions on the tracker; then `/change-request` sizes the effort: more than one epic continues at step 4. |
| 4 | Problem and brief | `/define-problem-statement`, then `/develop-solution-brief` | Both approved by the user. |
| 5 | Roadmap | `/user-story-mapping-workshop` | Story map cut into release slices; each slice is an epic. Approved. |
| 6 | Design, per epic | `/technical-writing`, then `/writing-design-docs` in the same session; ADRs through `domain-modeling`; `prototype` when a question needs running code | Design doc reviewed and approved. |
| 7 | PRD, per epic | `/deliver-prd <epic>` | PRD in the epic's home (project map). Approved. |
| 8 | Refinement, per story | `/specification <story>`, then `/story-splitting` when it is too big, then `/find-gaps` | Story ready: rules, examples and acceptance criteria agreed. |
| 9 | Tickets | `/to-tickets <epic, story or sized issue>` | Tickets with blocking edges, approved before publishing. |
| 10 | Build, per ticket | `/build-ticket <ticket>`; when pairing, `/pair <dials>` | PR open with the template filled. |
| 11 | Peer review, fresh session | `/code-review-and-quality <PR>`, then `gh pr checkout <PR> --detach` and `/security-review` (it reads the current branch's diff, so on main it finds nothing; `--detach` because the build's worktree may still hold the branch). When the user reviews: `/receiving-code-review`, then `/plannotator-review <PR>` | Verdict: approve or request changes. |
| 12 | Approval | `/acceptance-review <PR> against <ticket>`; CI green | The user merges: `gh stack merge <stack>` when `gh stack view` shows the PR in a stack, else `gh pr merge <PR>`. Then close the ticket's parent story or issue when this was its last open ticket; an epic closes at its retro. |
| 13 | Retro, per epic | `/epic-retro <epic>`, then `/retro` | Sourced findings, a verdict on the epic, action items. The epic closes once the user confirms the verdict. |

Approval gates are the user's: never treat a step as approved because its output exists. Steps 4 to 7, 9 and 12 have one: later steps build on what they produce, and at 12 the gate is the merge. With no ticket, the contract is the base branch's version of the doc the PR changes, and each line the PR rewrites in it goes to the user to approve before the merge. In the other steps the user takes part, but nothing waits for a sign-off. At the gates, the user's sizing preference applies: about 7 epics per roadmap and about 7 stories per epic, never more than 9. Past that, propose a split before approval.

## Ways in

- A feature, an improvement or a bug fix the user brings to an existing project: `/change-request <change>`.
- A bug report or request that arrived from outside: `/triage`. A bounded one it marks ready for an agent is already a ticket, built at step 10; anything bigger is marked ready for a human, and `/change-request <issue>` then sizes it from its brief, without a second grilling.
- Something broken that resists a first look: `diagnosing-bugs` loads on its own; for a hard one, `/diagnosing-bugs` explicitly.
- Production incident: `/engineering:incident-response`.
- A huge, foggy effort: `/wayfinder`. Once its map clears, `/change-request <effort>` sizes and places it, instead of going straight to step 4.

## Any time

`research` (a cited write-up of primary sources), `codebase-design` (deep-module vocabulary), `domain-modeling` (a contested term, an ADR), `wizard` (steps only the user can take), `lesson-learned`, `/handoff` (only when the work moves to another folder, tool or person).

## Sessions

One role per session, as on a team: product (steps 1 to 5, and `/change-request`), tech lead per epic (6 to 9), developer per ticket (10), reviewer per PR (11, always a fresh session). The tracker item is the hand-off between roles: the next session starts from its id, not from a summary. At a boundary inside one role, continue while the next phase needs this one's reasoning; otherwise clear. Keep steps 6 to 9 of one epic in one session when they fit.

## Maintenance

After installing, removing or updating a skill of this workflow, or changing this file, update [REGISTRY.md](REGISTRY.md), its Does line included, and run `python3 ~/.claude/skills/ask-team/scripts/check-registry.py`. It checks that every skill named here is in the registry, that each skill's visibility matches the settings, that no skill calls one Claude cannot load, and that the workflow page can still be built from this file and the registry. GitHub publishes that page on every push to `main`.
