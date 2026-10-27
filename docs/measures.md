# Measures

What the workflow measures about its own flow and quality, and how. Each measure is computed only because a named decision reads it (D56). No usage figure is recorded or computed anywhere: not per session, ticket or epic, and not in a baseline (section 7 of the decision record).

This file holds definitions only. The figures stay with the owner's private notes, because they name private projects' tickets; this repo is public.

## The measures

| Measure | Read by | Unit | From | To | Source | Traced today |
|---|---|---|---|---|---|---|
| Developer touches per merged ticket | Wave judgement (P12) | touches, by kind | the claim, or the first entry on the ticket's branch | the merge | `skills/ask-team/scripts/touches.py`, over the transcripts and the PR's and tracker item's events | yes, from the local transcripts; manual tracker moves and web comments only as listed events |
| Cycle time | Wave judgement (P12); service level expectations (D11, D12) | days worked, with wall-clock time beside it | the first move into a started state | the last move into a completed state | the tracker's state history | yes |
| Throughput | Service level expectations (D11, D12) | tickets completed per week | | | the tracker's state history | yes |
| WIP | Pull policy (D42) | started tickets and open PRs, at a date | | | the tracker's state history; the code host | yes |
| Item age | Pull policy (D42) | days since the item entered its current state | | | the tracker's state history | yes |
| PR wait | Pruning (D2) | wall-clock time, an upper bound | the PR opened, or marked ready when it was a draft | the merge | the code host | partly: it includes the review time, since nothing marks when the PR waits on the developer |
| Gate wait | Pruning (D2) | days | the document's first commit | the commit that adds its approval line | git | no: no approval line exists yet in a project's history |
| First-pass verdicts | Wave judgement (P12) | share of merged tickets whose first verdict asks for no required change, per check (acceptance, code review) | | | verdicts posted on the PR or the tracker item; otherwise the transcripts | partly: most verdicts are printed in the session, not posted |
| Findings fixed before merge, by rank | Wave judgement (P12); pruning (D2) | findings per rank (Required, Optional, FYI): raised, fixed before merge, deferred to a ticket, dismissed | | | the posted reviews; otherwise the transcripts | partly, for the same reason |
| Escaped defects | Wave judgement (P12); pruning (D2) | defects found after merge, traced to the merged ticket and the check that missed them | the merge | the defect's report | bug items linked to the PR they trace to (D43) | no: no bug item links to a PR yet |
| Accessibility failures caught before merge | Wave judgement (P12); pruning (D2) | failures per merged ticket that touches a screen | | | the accessibility check's results | no: no step checks a ticket's change for accessibility before merge; /ui-design's WCAG findings are on prototypes, not per merged ticket |

A measure that is not traced reads "not traced", never 0.

## Rules

- **Cycle time** ends at the last move into a completed state, never at a tracker's "completed at" field: a ticket moved to Done by hand and back keeps the first time there.
- **Days worked** follow D11: a day on which the ticket saw work, a commit, a PR event or a tracker change made by the developer or by a session they started; a day with only a little work counts in full, and scheduled jobs do not count. Days are taken in the developer's time zone. Until flow.py holds the one function that counts them (PR 43), each count states its time zone and method, and is recomputed with that function once it lands.
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

From PR 62, touches leave their own traces: a confirmation line on the tracker item and a dismissal line on the PR (P10). The first wave judgement after that counts both ways on the same tickets, and keeps both.

## Baselines and wave judgements

- **The wave-0 baseline** is taken after PR 1 (the pins) and before any other change (section 10). It covers the tickets merged on the workflow before it, and grows with every ticket merged on the pinned flow before wave 1's first PR merges, marked as such.
- **Each wave judgement** reads the same measures on the next real work and compares them with the baseline (P12). When a counting method changes, it is rerun on the baseline's tickets and both results are kept, so a change in method never reads as a change in the flow.
- **With a few tickets**, the judgement compares ticket by ticket against the baseline's range, never a single figure. P12's rule then applies as decided: a regression in touches or cycle time with no gain in any quality signal reverts the PRs behind it.
- **What a judgement cannot conclude yet:** gate wait, escaped defects and accessibility failures have no baseline, so a change in them is a first figure, not a gain or a loss. A check's fixed findings are its claimed benefit: they are weighed by rank and against its dismissals (P10), not counted as a gain by themselves.
