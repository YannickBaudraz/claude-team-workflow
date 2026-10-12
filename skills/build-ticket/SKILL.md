---
name: build-ticket
description: Build one ticket test-first on its own branch and open a pull request for review.
argument-hint: "<ticket id>"
disable-model-invocation: true
---

# Build ticket

One ticket, one branch, one pull request: the developer's role on a team. Reviewing it belongs to another session.

## 1. Load the ticket and its context

- Read the project map (the repo's `CLAUDE.md` or `AGENTS.md` points to it) and the tracker doc, `docs/agents/issue-tracker.md`.
- Fetch the ticket: its body, acceptance criteria, comments, parent story or epic, and blockers. State its title to the user. When a blocker is still open, stop and say which.
- Read `GLOSSARY.md`, the ADRs touching this area, `CODING_STANDARDS.md` and the definition of done.

Done when you can list every acceptance criterion and the files and seams it touches.

## 2. Branch

Create one branch for the ticket, named as the tracker doc says; without a convention, use `<ticket-id>-<short-slug>`. When other tickets are being built in parallel, work in a worktree.

## 3. Build test-first

Read both files fully and follow them:

- `~/.claude/skills/incremental-implementation/SKILL.md`
- `~/.claude/skills/test-driven-development/SKILL.md`

Each acceptance criterion is a slice: red, green, refactor, using the project's own test commands. Before each commit, show the user the change and the message, then commit once they approve. Messages are written as the user would write them, with no attribution to any tool or assistant.

Done when every acceptance criterion has a test that failed before its slice and passes now.

## 4. Verify

Run the full test suite, type check, lint and build with the project's commands. Check every item of the definition of done that applies before review. Done when everything is green and each criterion has its evidence.

## 5. Open the pull request

Read `~/.claude/skills/finishing-a-development-branch/SKILL.md` and follow it, recommending *push and create a pull request*. Write the body from the repo's pull request template, link the ticket, and move the ticket to the review state the tracker doc names.

Then tell the user the next step: review in a **fresh session** with `/code-review-and-quality <PR>`.
