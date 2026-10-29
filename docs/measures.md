# Measures

What the workflow measures about its own flow and quality, and how. A measure is computed only when something uses it, named in the *Used for* column. No usage figure is recorded or computed anywhere: not per session, ticket or epic.

This file holds definitions only. The figures are kept out of this repo, because it is public and they name private projects' tickets.

## The measures

| Measure | Used for | Unit | From | To | Source | Traced today |
|---|---|---|---|---|---|---|
| Developer touches per merged ticket | judging a change to the workflow | touches, by kind | the claim, or the first entry on the ticket's branch | the merge | `skills/ask-team/scripts/touches.py`, over the transcripts and the PR's and tracker item's events | yes, from the local transcripts; manual tracker moves and web comments only as listed events |
| Cycle time | judging a change to the workflow; how long tickets and epics take | days worked, with wall-clock time beside it | the first move into a started state | the last move into a completed state | the tracker's state history | yes |
| Throughput | how long tickets and epics take | tickets completed per week | | | the tracker's state history | yes |
| WIP | how much work is in flight at once | started tickets and open PRs, at a date | | | the tracker's state history; the code host | yes |
| Item age | how much work is in flight at once | days since the item entered its current state | | | the tracker's state history | yes |
| PR wait | whether a step earns its cost | wall-clock time, an upper bound | the PR opened, or marked ready when it was a draft | the merge | the code host | partly: it includes the review time, since nothing marks when the PR waits on the developer |
| Gate wait | whether a step earns its cost | days | the document's first commit | the commit that adds its approval line | git | no: no approval line exists yet in a project's history |
| First-pass verdicts | judging a change to the workflow | share of merged tickets whose first verdict asks for no required change, per check (acceptance, code review) | | | verdicts posted on the PR or the tracker item; otherwise the transcripts | partly: most verdicts are printed in the session, not posted |
| Findings fixed before merge, by rank | judging a change to the workflow; whether a step earns its cost | findings per rank (Required, Optional, FYI): raised, fixed before merge, deferred to a ticket, dismissed | | | the posted reviews; otherwise the transcripts | partly, for the same reason |
| Escaped defects | judging a change to the workflow; whether a step earns its cost | defects found after merge, traced to the merged ticket and the check that missed them | the merge | the defect's report | bug items linked to the PR they trace to | no: no bug item links to a PR yet |
| Accessibility failures caught before merge | judging a change to the workflow; whether a step earns its cost | failures per merged ticket that touches a screen | | | the accessibility check's results | no: no step checks a ticket's change for accessibility before merge; /ui-design's WCAG findings are on prototypes, not per merged ticket |

A measure that is not traced reads "not traced", never 0.

## Rules

- **Cycle time** ends at the last move into a completed state, never at a tracker's "completed at" field: a ticket moved to Done by hand and back keeps the first time there.
- **Days worked**: a day on which the ticket saw work, a commit, a PR event or a tracker change made by the developer or by a session they started; a day with only a little work counts in full, and scheduled jobs do not count. Days are taken in the developer's time zone, and each count states its time zone and method.
- **A first pass** means the first verdict asks for no required change. "Approve once the change is made" is not a first pass.
- **Findings** are counted by the rank the review gave them; a nit counts in the rank it is listed under, and a finding with no rank is counted apart. A finding deferred to a new ticket, or to another ticket's criteria, counts as deferred, not fixed.
- **An escaped defect** is a defect found after the merge of the ticket it traces to. A defect found within 14 days of the merge counts in that ticket's figures; one found later is added with its date.
- **Bots and scheduled jobs** are left out: dependency updates, CI, integrations that move a ticket on merge.

## Developer touches

A touch is one act by the developer on one ticket's work, up to its merge, counted once:

- **prompt**: a prompt or slash command the developer typed in a session working on the ticket, including one typed while the agent was working: its build session, and the review and acceptance sessions of its PR;
- **shell**: a command the developer ran in shell mode (`!`) in such a session;
- **outside**: an act on the ticket's PR or tracker item that no session made, such as a status changed by hand or a comment typed on the web;
- **merge**: the merge, exactly one, whether made in a session, in shell mode or on the web. The shell command that merged, or the prompt that asked an agent to merge, is that merge and is not counted again; an earlier attempt that failed is a shell touch.

Not touches: what an agent runs, even under the developer's login (commits, PRs, reviews, comments, tracker saves, merges it makes when asked), tool results, skill bodies, command output, notifications, interrupts, subagents, bots, reading and waiting.

The code host and the tracker cannot tell the developer's acts from an agent's: both act under the developer's login. Only the local transcripts can, so `touches.py` reads them and prints counts only. It reads a list of entry fields and, from each message, only the text a user entry carries, an agent's commands, tool names and the item id a tracker tool was given; never a usage or cost field.

An entry belongs to the item its session last named, in a prompt, a shell command or an agent's command: a ticket's id or PR number, or another item, which leaves the entry to no ticket. Until its session names an item, an entry belongs to the ticket whose branch or worktree it ran in. Entries on the ticket's branch count from the branch's first entry, others from the claim. Two limits: a session that moves to other work without naming it keeps counting for the ticket, and acts made outside any session are seen only through the PR's and tracker item's events.

## Judging a change to the workflow

- **A change is judged** on these measures, on the tickets merged after it against those merged before it. When a counting method changes, it is rerun on the earlier tickets and both results are kept, so a change in method never reads as a change in the flow.
- **With a few tickets**, the comparison goes ticket by ticket against the earlier tickets' range, never a single figure. A regression in touches or cycle time with no gain in any quality measure (first-pass verdicts, findings fixed, escaped defects, accessibility failures) reverts the change behind it.
- **What a comparison cannot conclude yet:** gate wait, escaped defects and accessibility failures have no earlier figures, so a change in them is a first figure, not a gain or a loss. A check's fixed findings are its claimed benefit: they are weighed by rank and against the findings it dismissed, not counted as a gain by themselves.
