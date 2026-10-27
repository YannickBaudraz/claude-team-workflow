# Ask team: the flow

The steps, what each needs and leaves behind, and who works them. Both readings use it: the full one in [ROUTER.md](ROUTER.md), and the light one in [SKILL.md](SKILL.md).

## Main flow

| # | Step | Command | Output, and the gate before moving on |
|---|---|---|---|
| 1 | Discovery | `/grill-with-docs <idea>` (before any project folder exists: `/grill-me`) | Shared understanding; glossary terms and ADRs in the repo. Reads the domain doc first when one exists. |
| 2 | Setup | `/project-setup`, then `/setup-matt-pocock-skills` | Project map, tracker doc, conventions. |
| 3 | Fog (only when the way is unclear) | `/wayfinder <map>` to continue a map, `/wayfinder` alone to chart one; then `/change-request <map>` once it clears | Decisions on the tracker, and the effort sized: more than one epic continues at step 4. |
| 4 | Problem and brief | `/define-problem-statement`, then `/develop-solution-brief` | Both approved by the user. |
| 5 | Roadmap | `/user-story-mapping-workshop` | Story map cut into release slices; each slice is an epic. Approved. |
| 6 | PRD, per epic | `/deliver-prd <epic>` | PRD where the project map puts PRDs, saying which screens the epic adds or changes, if any; each story in the tracker with the outcome it delivers. Approved. |
| 7 | Technical design, per epic | `/technical-writing`, then `/writing-design-docs <epic>` in the same session; ADRs through `domain-modeling`; `prototype` when a question needs running code | Design doc reviewed and approved. |
| 8 | Interface design, per epic (only when the epic has a user interface) | `/ui-design <epic>` | The epic's interface design: directions sketched, then merged with the user. When the product has no visual direction yet, its visual direction too. Approved. |
| 9 | Refinement, per story | `/specification <story>`, then `/story-splitting` when it is too big, then `/find-gaps` | Story ready: rules, examples and acceptance criteria agreed. |
| 10 | Tickets | `/to-tickets <epic, story or sized issue>` | Tickets with blocking edges, approved before publishing. |
| 11 | Build, per ticket | `/build-ticket <ticket>`; when pairing, `/build-ticket <ticket> pair <dials>` | PR open with the template filled. |
| 12 | Review, fresh session | `/code-review-and-quality <PR>`, then `gh pr checkout <PR> --detach` and `/security-review`. When the user reviews: `/receiving-code-review`, then `/plannotator-review <PR>` | Verdict: approve or request changes. |
| 13 | Approval | `/acceptance-review <PR> against <ticket>`; CI green. To merge: `gh stack merge <stack>` when `gh stack view` shows the PR in a stack, else `gh pr merge <PR>` | The user merges, in a terminal or in shell mode (!): in a project set up with the workflow, its settings make the agent refuse the merge, a push to the default branch and a branch rule change, a filter against mistakes rather than a lock. After the merge, the user closes the ticket's parent story or issue when this was its last open ticket; an epic closes at its retro. |
| 14 | Retro, per epic | `/epic-retro <epic>`, then `/retro` | Sourced findings, a verdict on the epic, action items. The epic closes once the user confirms the verdict. |

In these commands, `<epic>`, `<story>`, `<ticket>`, `<map>` and `<issue>` stand for the item's id, written the way the tracker doc writes ids, never a file name or a title.

Approval gates are the user's: never treat a step as approved because its output exists. A document is approved when it ends with the line `Approved by <name> on <date>`, which the step's skill writes when the user approves it in the session; tickets are approved by being published, and step 13 by the merge. A document without that line is waiting for approval, however finished it looks, and the user approves it by running its step's command again: that session writes the line and does what follows the approval, such as creating the stories. Steps 4 to 8, 10 and 13 have one, step 8 only when it runs: later steps build on what they produce, and at 13 the gate is the merge. A later step that finds an approved document wrong proposes the change; it holds once the user approves it in that document's step, run again on the approved document. Step 8 runs when the project map gives interface designs a home and the epic's PRD names screens it adds or changes; otherwise the epic goes from step 7 to step 9. With no ticket, the contract is the base branch's version of the doc the PR changes, and each line the PR rewrites in it goes to the user to approve before the merge. In the other steps the user takes part, but nothing waits for a sign-off. At the gates, the user's sizing preference applies: about 7 epics per roadmap and about 7 stories per epic, never more than 9. Past that, propose a split before approval.

## Step contracts

What each step needs before it starts and what it leaves behind. A way in is a row too: what it makes is there for any step after setup. `scripts/check-contracts.py` checks that every need is made by an earlier step or a way in (a need marked *when* applies only in that case), that each maker says it makes its output, and that every home is a row of the project map.

| Step | Needs | Makes |
|---|---|---|
| 1 | idea (outside) | glossary terms, ADRs |
| 2 | — | project map, tracker doc, definition of done, coding standards, PR template |
| 3 | effort (outside), project map | decision tickets, sized issue |
| 4 | project map | problem statement, solution brief |
| 5 | solution brief | story map, epic |
| 6 | epic | PRD, story |
| 7 | epic, PRD | design doc, ADRs |
| 8 | epic, PRD, design doc | interface design, visual direction |
| 9 | story, interface design (when the epic has a user interface) | refined story |
| 10 | refined story or sized issue or epic | ticket |
| 11 | ticket, definition of done, coding standards, PR template | pull request |
| 12 | pull request, ticket, coding standards | review |
| 13 | pull request, review, ticket | merged pull request |
| 14 | epic, PRD, merged pull request | retro |
| `/change-request` | change (outside) or triaged issue, project map | sized issue, story, epic |
| `/triage` | report (outside), tracker doc | triaged issue, ticket |

| Output | Made by | Lives in |
|---|---|---|
| glossary terms | `/grill-with-docs`, `domain-modeling` | Glossary for this repo's code |
| ADRs | `/grill-with-docs`, `domain-modeling` | ADRs |
| project map | `/project-setup` | Documentation |
| tracker doc | `/setup-matt-pocock-skills` | `docs/agents/issue-tracker.md` |
| definition of done | `/project-setup` | Definition of done |
| coding standards | `/project-setup` | Coding standards |
| PR template | `/project-setup` | Code host |
| decision tickets | `/wayfinder` | Issue tracker |
| sized issue | `/change-request` | Issue tracker |
| triaged issue | `/triage` | Issue tracker |
| problem statement | `/define-problem-statement` | Problem statement and solution brief |
| solution brief | `/develop-solution-brief` | Problem statement and solution brief |
| story map | `/user-story-mapping-workshop` | Roadmap |
| epic | `/user-story-mapping-workshop`, `/change-request` | Epics, stories and tickets |
| PRD | `/deliver-prd` | PRDs |
| design doc | `/writing-design-docs` | Design docs |
| interface design | `/ui-design` | Interface designs |
| visual direction | `/ui-design` | Visual direction |
| story | `/deliver-prd`, `/change-request` | Epics, stories and tickets |
| refined story | `/specification` | Epics, stories and tickets |
| ticket | `/to-tickets`, `/triage` | Epics, stories and tickets |
| pull request | `/build-ticket` | Code host |
| review | `/code-review-and-quality` | Code host |
| merged pull request | the user | Code host |
| retro | `/epic-retro` | Retros |

## Sessions

One role per session, as on a team: product owner (steps 1, 3 to 6, and `/change-request`), architect (2), architect per epic (7), interface designer per epic (8, only when it runs), architect per epic (9 to 10), developer per ticket (11), reviewer per PR (12, always a fresh session). At refinement, the product owner answers the specification's questions in the architect's session. The tracker item is the hand-off between roles: the next session starts from its id, not from a summary. At a boundary inside one role, continue while the next phase needs this one's reasoning; otherwise clear. Keep steps 9 and 10 of one epic in one session when they fit. When `/change-request` finds no project map, setup runs in its session. Build sessions never run in a cloud thread of a Claude project or in a cloud session on several repositories: those read none of a repository's permission rules or hooks, so nothing would keep the merge from the agent.
