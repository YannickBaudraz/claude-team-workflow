---
name: build-ticket
description: Build one ticket test-first on its own branch and open a pull request for review.
argument-hint: "<ticket id> [pair <dials>]"
disable-model-invocation: true
---

# Build ticket

One ticket, one branch, one pull request: the developer's role on a team. Reviewing it belongs to another session.

## 1. Load the ticket and its context

- Read the project map (the repo's `CLAUDE.md` or `AGENTS.md` points to it) and the tracker doc, `docs/agents/issue-tracker.md`.
- Fetch the ticket: its body, acceptance criteria, comments, parent story or epic, and blockers. State its title to the user. When a blocker is still open, stop and say which.
- Read `GLOSSARY.md`, the ADRs touching this area, and the coding standards and definition of done where the project map puts them.

Done when you can list every acceptance criterion and the files and seams it touches.

## 2. Claim and branch

Two tracker states come before the build (in Linear: Backlog and Todo):

- **Waiting** holds what no one can build yet: specs, stories, untriaged issues, issues still waiting for their next command, and tickets with an open blocker.
- **Ready** holds the tickets this skill could start now: made by `/to-tickets` or marked `ready-for-agent` by triage, every blocker closed, no one assigned.

Before creating the branch, update the tracker, unless the tracker doc says otherwise:

- **Promote.** Move each waiting ticket that is now ready to the ready state, for the whole project; specs, stories and other issues never move. A merge closes a blocker with no session there to promote what it unblocked, so every build start does it. Tell the user which tickets moved.
- **Claim.** Assign this ticket to the user and move it to the tracker's started state (in Linear: In Progress).

Use the state names the tracker doc gives. When the tracker has no such states, only assign the ticket.

Create one branch for the ticket, named as the tracker doc says; without a convention, use `<ticket-id>-<short-slug>`. When other tickets are being built in parallel, work in a worktree.

## 3. Build test-first

Read both files fully and follow them:

- `~/.claude/skills/incremental-implementation/SKILL.md`
- `~/.claude/skills/test-driven-development/SKILL.md`

Each acceptance criterion is a slice: red, green, refactor, using the project's own test commands. Before each commit, show the user the change and the message, then commit once they approve. Messages are written as the user would write them, with no attribution to any tool or assistant.

When the arguments include `pair <dials>`, also read `~/.claude/skills/pair/SKILL.md` fully and work every slice under those dials. Pairing changes how this step is worked with the user, not the steps around it: the ticket is still claimed, verified and opened as a pull request as below.

Done when every acceptance criterion has a test that failed before its slice and passes now.

## 4. Verify

Run the full test suite, type check, lint and build with the project's commands. Check every item of the definition of done that applies before review. Done when everything is green and each criterion has its evidence.

## 5. Open the pull request

Read `~/.claude/skills/finishing-a-development-branch/SKILL.md` and follow it, recommending *push and create a pull request*. Write the body from the repo's pull request template, link the ticket, and move the ticket to the review state the tracker doc names.

Then tell the user the next step: review in a **fresh session** with `/code-review-and-quality <PR>`.
