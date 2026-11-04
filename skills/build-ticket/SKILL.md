---
name: build-ticket
description: Build one ticket test-first on its own branch and open a pull request for review.
argument-hint: "<ticket id> [pair <dials>]"
disable-model-invocation: true
---

# Build ticket

One ticket, one branch, one pull request: the developer's role on a team. Reviewing it belongs to another session. When the reviews send the ticket back, the rework is this skill's too: when the ticket's pull request is already open, or on the private path its branch has review verdicts on the private record, go to step 6 once step 1 is done.

## 1. Load the ticket and its context

- Read the project map (the repo's `CLAUDE.md` or `AGENTS.md` points to it) and the tracker doc, `docs/agents/issue-tracker.md`.
- Fetch the ticket: its body, acceptance criteria, comments, parent story or epic, and blockers. State its title to the user. When a blocker is still open, stop and say which.
- Read `GLOSSARY.md`, the ADRs touching this area, and the coding standards and definition of done where the project map puts them.
- **A ticket on the private path.** When the ticket, or the issue it belongs to, has a `Private record: <link>` line, it fixes a weakness not yet disclosed (`/change-request`, The private path). Check the visibility of the ticket's repository, the one the project map names (for a GitHub issue, the one in its URL), with `gh repo view <owner>/<repo> --json visibility`. On a private repository, the ticket builds as any other. On a public repository, it is on **the private path**, which steps 4 to 6 follow, because a branch of a public repository is public: it is built only in a clone of a draft advisory's temporary private fork.
  - **This folder is that clone** when `git remote -v` lists one remote, and `gh repo view --json visibility` here says private while the ticket's repository says public. Go on, and read the acceptance criteria from the private record.
  - **Otherwise, stop.** Only a draft advisory can start the fork: when the private record is a private document with no draft advisory beside it, ask the user to open one on the repository (on GitHub: the Security tab, then Advisories, then New draft security advisory), linked from the document. Ask the user to start the fork from the advisory when it has none (on GitHub: Start a temporary private fork), clone it into a new folder, and run this skill again there.

Done when you can list every acceptance criterion and the files and seams it touches.

## 2. Claim and branch

Two tracker states come before the build (in Linear: Backlog and Todo):

- **Waiting** holds what no one can build yet: specs, stories, untriaged issues, issues still waiting for their next command, and tickets with an open blocker.
- **Ready** holds the tickets this skill could start now: made by `/to-tickets` or marked `ready-for-agent` by triage, every blocker closed, no one assigned.

Before creating the branch, update the tracker, unless the tracker doc says otherwise:

- **Promote.** Move each waiting ticket that is now ready to the ready state, for the whole project; specs, stories and other issues never move. A merge closes a blocker with no session there to promote what it unblocked, so every build start does it. Tell the user which tickets moved.
- **Claim.** Assign this ticket to the user and move it to the tracker's started state (in Linear: In Progress).

Use the state names the tracker doc gives. When the tracker has no such states, only assign the ticket.

The claim lasts until the pull request moves the ticket to review. When the build stops before that, tell the user the ticket is still claimed, and unassign it and move it back to the ready state unless they keep it.

Create one branch for the ticket, named as the tracker doc says; without a convention, use `<ticket-id>-<short-slug>`. When other tickets are being built in parallel, work in a worktree.

## 3. Build test-first

Read both files fully and follow them:

- `~/.claude/skills/incremental-implementation/SKILL.md`
- `~/.claude/skills/test-driven-development/SKILL.md`

Each acceptance criterion is a slice: red, green, refactor, using the project's own test commands. Before each commit, show the user the change and the message, then commit once they approve. Messages are written as the user would write them, with no attribution to any tool or assistant.

When the arguments include `pair <dials>`, also read `~/.claude/skills/pair/SKILL.md` fully and work every slice under those dials. Pairing changes how this step is worked with the user, not the steps around it: the ticket is still claimed, verified and opened as a pull request as below. No dial lifts the approval before each commit, `autonomy=weapons-free` included.

Done when every acceptance criterion has a test that failed before its slice and passes now.

## 4. Verify

Run the full test suite, type check, lint and build with the project's commands. Check every item of the definition of done that applies before review. On the private path, no CI reaches the fork: these checks, run here, stand in for it. Done when everything is green and each criterion has its evidence.

## 5. Open the pull request

Except on the private path, below: read `~/.claude/skills/finishing-a-development-branch/SKILL.md` and follow it, recommending *push and create a pull request*. Write the body from the repo's pull request template, link the ticket, and move the ticket to the review state the tracker doc names.

Then, except on the private path, tell the user the next step: once CI is green, the review chain in a **fresh session**, starting with `/acceptance-review <PR> against <ticket>`. The code review and the security review follow in that same session, unless the acceptance verdict sends the ticket back.

**On the private path**, push the branch to the fork and nowhere else: from this session when its code-host token reaches the fork, otherwise the user pushes it. Open no pull request, and comment nothing about the fix on the public issue; move the ticket to the review state the tracker doc names, without a comment. Then tell the user the next step: the review chain in a **fresh session** opened in the fork's clone, against this branch, starting with `/acceptance-review <branch> against <ticket>`, which reads the criteria from the private record; the code review and the security review follow in that same session. Its verdicts and findings stay in that session and on the private record, never on the public issue. On GitHub, a temporary private fork's pull requests are opened and merged only from the advisory: Compare & pull request, then Merge pull request(s). Tell the user that this merge is theirs, in the web interface, and that GitHub enforces no branch rule there and runs no CI, so the checks this session ran and the user's read of the full diff at that merge stand in for CI and the branch rule at that merge. The fix lands with the release, and publishing the advisory is the user's act too.

## 6. Rework

Except on the private path, below: the ticket's pull request is open and its reviews sent it back: a comment starting `VERDICT: does-not-satisfy`, or a review that requests changes. The latest verdict of each review is the one that holds; when none of them sends the ticket back, tell the user what the pull request waits for instead and stop.

- **Count the rounds.** Each verdict on the pull request that sent the ticket back is one. A ticket gets at most two: with a third, stop, tell the user it has used both, and that they re-spec its story with `/specification <story>` or split the ticket with `/to-tickets <story>`.
- **Take in the findings** of the reviews that sent it back, all of them, on the pull request's branch (in its worktree when it has one). Check each one before changing code; a finding you decline gets its reason.
- **Answer them in this one round**, as in step 3: a finding about behaviour gets its failing test first, and each commit waits for the user's approval.
- **Verify** as in step 4 and push. Comment on the pull request what each finding got: the commit that answers it, or why it was declined. The ticket stays in review.

Then tell the user the next step: the whole chain again once CI is green, in a **fresh session**, starting with `/acceptance-review <PR> against <ticket>`.

**On the private path** there is no pull request until the user's merge from the advisory, and no CI: the verdicts that send the ticket back are those the review session put on the private record, against the branch. Count the rounds from them, with the same cap. Take in and answer the findings as above, on the branch in the fork's clone, verify as in step 4, and push to the fork alone. Record what each finding got on the private record, never on the pull request or the public issue. Then tell the user the next step: the whole chain again in a **fresh session** in the fork's clone, starting with `/acceptance-review <branch> against <ticket>`.
