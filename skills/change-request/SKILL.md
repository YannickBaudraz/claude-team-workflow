---
name: change-request
description: Bring a feature, an improvement, a bug fix, an incident's fix or a postmortem's actions into an existing project: diagnose or grill it as needed, size it with the user, and write it as one issue with the next command, or one per action for a postmortem.
argument-hint: "<change, or its issue, or a postmortem>"
disable-model-invocation: true
---

# Change request

The way in for one change to a project that already exists: a feature, an improvement or a bug fix, a production incident's fix included. It is the product owner's intake: the change leaves **sized** and written as one issue on the tracker, and the next session starts from that issue's id. The issue keeps its id to the end: it becomes the parent of its ticket, a story, or the epic itself.

Two cases change the sections below, each in its own section at the end: a postmortem's actions, all taken in one session, and a suspected security incident or vulnerability, which takes the private path.

Step numbers below are the main flow's, in `~/.claude/skills/ask-team/FLOW.md`; read its Main flow, and How to route in `ROUTER.md` beside it, before starting.

## 1. Read the state

Read the project map (the repo's `CLAUDE.md` or `AGENTS.md` points to it) and the tracker doc it names, with its label names, then find the solution brief, the roadmap, and each open epic with the step it has reached. When the argument is an issue, read it with its comments: a triage brief or a spike's answer there counts as the interview, and the change goes straight to sizing.

With no project map yet, the user types `/project-setup`, then `/setup-matt-pocock-skills`, in this session, and the change continues once the tracker exists. When the user is not sure the change is worth doing, the interview without docs (section 3) comes before setup, and a dropped change ends there.

Done when you know the tracker, whether a brief and a roadmap exist, and the step of every open epic.

## 2. Diagnose a bug

For a bug whose cause is unknown, call the Skill tool with `diagnosing-bugs` and stop once the cause is confirmed: the fix is built later, from the ticket. A production incident's fix is diagnosed the same way, once the user has mitigated it, and its reproduction becomes the failing regression test the fix starts from. A bug with a known cause, a feature and an improvement go straight to the next section.

Done when a reproduction confirms the cause.

## 3. Interview a fuzzy change

When you cannot yet tell whether the change is a spike, a bounded change or an architectural one, interview the user. Pick the interview from the situation, tell the user which, and switch when they ask:

- **With docs**, as `/grill-with-docs` runs it: call the Skill tool with `grilling` and `domain-modeling`. For a change that brings new domain terms or decisions into a project that keeps a glossary or ADRs.
- **Without docs**, as `/grill-me` runs it: call the Skill tool with `grilling`. For testing whether the change is worth doing before anything is written to the repo.

A change dropped here leaves nothing behind: no issue, no note.

Done when the user confirms a shared understanding and you can name the change's size.

## 4. Size and place

Propose the size, as Size the request defines it in the router, and where the change goes:

- **Spike**: `prototype` or `research` answers it. Its Next line reads: answer it with `research` or `prototype`, comment the answer on this issue with a link to the notes when there are any, then `/change-request <issue>` to size it again.
- **Bounded**: one ticket, written by `/to-tickets <issue>` at step 10.
- **Fits an open epic** not yet at step 10: a story of that epic, its issue a sub-issue of the epic's. Its Next line is `/deliver-prd <epic>`: the PRD takes the story in, and is approved again when it was approved already. The story is then refined at step 9 with the others.
- **Its own epic**: the issue becomes the epic, which starts at step 6. Before that, revisit the solution brief at step 4 when the change falls outside it, and when the project has a roadmap, propose where the new slice goes among those not started: the user places it at the approval, and the story map is edited by hand. A project without a roadmap does not need one for a single epic.
- **More than one epic**: steps 4 and 5, with `/wayfinder` first when the way is unclear. The issue becomes the parent of the epic issues the roadmap creates.

Done when the user confirms both the size and the place.

## 5. Write the issue

Write one issue on the tracker, or update the one given as the argument: what the change is, what was decided, what is still open, then two lines, `Size: <size>` and `Next: <command with its arguments>`. Label it `bug` or `enhancement`, and `ready-for-human`, under the names the tracker doc gives those labels, so triage and unattended agents leave it to the next session. A story's issue gets its epic's issue as parent.

A production incident's fix is expedite work: the issue says so, so that it is built before every other item in flight, and says that the fix starts from a failing regression test made from the reproduction.

Done when the issue exists with both lines, its two labels, and its parent when it has one.

## 6. Hand over

Tell the user the issue's id, the next command from its Next line, and the session to run it in, as Sessions in FLOW.md assigns roles: the next role starts a fresh session from the issue's id.

## A postmortem's actions

When the argument is a postmortem, this one session takes all of its actions, and writes one sized issue per action. This is the one case where this skill writes more than one issue.

- Read the state as in section 1, then the postmortem and each of its actions. Size each action as in section 4. An action that needs grilling or a spike is not settled here: it becomes its own issue, whose Next line is `/change-request <issue>`, and that issue counts as the action's filed issue, so the postmortem can link it.
- Each issue says what will prove its action done:
  - an action that changes the product's behaviour starts from a failing regression test, at the seam the project's test strategy sets, or else where users met the defect: a defect users met on a screen is tested at the UI seam;
  - an action on detection, a runbook or recovery names the executed check that proves it: an alert fired by a deliberate failure, a drill run, or a runbook run.
- Show the user every issue together, and write them once they confirm the set, each as section 5 writes one.
- For a security incident, each issue keeps a neutral public title, and a security fix's failing test stays on the private record until the release, as the private path below says.

Done when every action has its issue, with its two lines and its labels, and the user has the list of ids to link from the postmortem.

## The private path

For a suspected security incident or vulnerability, live or only reported, and for any change the router printed with `(private path)`. Everything that describes the weakness stays in a private place until the fix is released and everyone who must be told has been: the report, the reproduction command, the investigation notes, the failing regression test and the fix.

- **The private record.** The private place is the repository and its tracker when both are private. Otherwise it is a draft security advisory on the repository (on GitHub: the Security tab, then Advisories, then New draft security advisory), or a private document the user names. Ask the user for its link, or to open the draft advisory when there is none. Every detail goes there, never on a public tracker; for a security incident, so do its item and its log.
- **The public issue.** On a public tracker, the issue states the outcome under a neutral title that names no weakness, with no exploit detail and no reproduction, and gets the line `Private record: <link>` above its Size and Next lines. `/build-ticket` reads that line.
- **Sizing.** Size the change on the private record. On a public tracker, nothing is broken into tickets there: a bounded fix's Next line is `/build-ticket <issue>`, with its acceptance criteria and its failing regression test on the private record, and anything bigger is planned on the private record.
- **Nothing public before the release.** On a public repository, nothing of it is pushed to the repository or opened there as a pull request before the release: `/build-ticket` builds it in a draft advisory's temporary private fork, so a private record kept in a document also gets a draft advisory when the build starts. After the release, the public record is the advisory, which the user publishes, and the release note's Security entry.

Done when the details are on the private record, and any public issue has its neutral title and its `Private record:` line.
