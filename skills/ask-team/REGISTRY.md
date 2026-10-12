# Registry

Every skill the team workflow names, and how it is reached. `scripts/check-registry.py` reads the tables below, so keep their columns.

**Visibility** says who can start the skill:

- `typed`: command-only by its own frontmatter; only the user starts it.
- `hidden`: command-only through `skillOverrides: "user-invocable-only"` in `~/.claude/settings.json`; only the user starts it.
- `auto`: Claude may load it on its own, and other skills may call it.
- `denied`: blocked for Claude by `permissions.deny`; the user can still type it.
- `built-in`: ships with Claude Code.

A skill may only **call** an `auto` or `built-in` skill: Claude Code refuses a call to a `typed` or `hidden` one. `file:` marks a skill read directly from disk, which works whatever its visibility.

**Arguments** are appended to the command when the router prints it, so the skill follows this workflow's conventions instead of its own defaults. The project map is the per-project document that says which tools the project uses and where each kind of document lives; the tracker doc is `docs/agents/issue-tracker.md`.

## Workflow skills

| Command | Source | Visibility | Used at | Calls | Arguments |
|---|---|---|---|---|---|
| `/ask-team` | ours | typed | any time | | |
| `/project-setup` | ours | typed | 2 Setup | | |
| `/build-ticket` | ours | typed | 10 Build | file:incremental-implementation, file:test-driven-development, file:finishing-a-development-branch | `<ticket id>` |
| `/epic-retro` | ours | typed | 13 Retro | lesson-learned | `<epic id>` |
| `/grill-with-docs` | matt | typed | 1 Discovery | grilling, domain-modeling | Read the domain doc first if the project map names one. |
| `/grill-me` | matt | typed | 1 Discovery, before any folder | grilling | |
| `grilling` | matt | auto | under grill-with-docs, triage, wayfinder | | |
| `domain-modeling` | matt | auto | glossary terms and ADRs, any time | | The domain doc wins over the repo glossary on meaning; raise a disagreement with its owner. |
| `/setup-matt-pocock-skills` | matt | typed | 2 Setup | | Tracker, labels and glossary layout as the project map says. |
| `/wayfinder` | matt | typed | 3 Fog | grilling, domain-modeling, prototype, research | When the map clears, continue at step 4, not /to-spec. |
| `/define-problem-statement` | personal | hidden | 4 Problem | | Save where the project map puts the problem statement. |
| `/develop-solution-brief` | personal | hidden | 4 Brief | | Save where the project map puts the solution brief. |
| `/user-story-mapping-workshop` | personal | hidden | 5 Roadmap | file:workshop-facilitation, file:user-story-mapping | Each release slice becomes one epic. Stop at the map; stories are refined at step 8. |
| `workshop-facilitation` | personal | auto | under the workshop | | |
| `/user-story-mapping` | personal | hidden | read by the workshop | | |
| `/technical-writing` | personal | hidden | 6 Design | | Use it as the writing style only; leave CLAUDE.md unchanged. |
| `/writing-design-docs` | personal | hidden | 6 Design | | Run after /technical-writing in the same session. Record decisions as ADRs with domain-modeling. Save where the project map puts design docs. |
| `prototype` | matt | auto | 6 Design | | |
| `frontend-design:frontend-design` | plugin:frontend-design | auto | 6 Design, UI only | | |
| `/deliver-prd` | personal | hidden | 7 PRD | | `<epic>`. Save in the epic's home from the project map. About 7 user stories, never more than 9; detail goes into requirements and acceptance criteria. |
| `/specification` | personal | hidden | 8 Refinement | | `<story>`. The story lives in the tracker. Open decisions go to /grill-with-docs; new terms to domain-modeling. |
| `/story-splitting` | personal | hidden | 8 Refinement | | Hand the chosen slices to /to-tickets. |
| `/find-gaps` | personal | hidden | 8 Refinement | | Write the closed gaps back into the story in the tracker. |
| `/to-tickets` | matt | typed | 9 Tickets | | `<epic or story>`. Tickets the user will build themselves get `ready-for-human`. |
| `/pair` | personal | hidden | 10 Build, pairing | | `role=… detail=… autonomy=…` |
| `test-driven-development` | personal | hidden | read by /build-ticket | | |
| `incremental-implementation` | personal | hidden | read by /build-ticket | | |
| `finishing-a-development-branch` | personal | hidden | read by /build-ticket | | |
| `tdd` | matt | auto | ad-hoc test-first work | codebase-design | |
| `codebase-design` | matt | auto | any time | | |
| `pr` | matt | auto | PR bodies | | |
| `/code-review-and-quality` | personal | hidden | 11 Review | | `<PR>`. Against the ticket's acceptance criteria and CODING_STANDARDS.md. Post the findings on the PR. |
| `code-review` | matt | auto | ad-hoc reviews | | |
| `/security-review` | built-in | built-in | 11 Review | | |
| `receiving-code-review` | personal | auto | 11 Review, acting on feedback | | |
| `/plannotator-review` | personal | typed | 11 Review, the user reviews | | `<PR or worktree>` |
| `/acceptance-review` | personal | hidden | 12 Approval | | `<PR> against <ticket>`. The ticket is the authoritative contract. |
| `/ci-cd-and-automation` | personal | hidden | 2 Setup, once per project | | For the code host in the project map. Show each commit and wait for approval. |
| `/retro` | matt | typed | 13 Retro | writing-for-agents | The sessions of the epic just closed. |
| `writing-for-agents` | matt | auto | editing skills or CLAUDE.md | | |
| `lesson-learned` | personal | auto | 13 Retro, any time | | |
| `/triage` | matt | typed | way in | grilling, domain-modeling | |
| `diagnosing-bugs` | matt | auto | way in | | |
| `engineering:incident-response` | synced:engineering | auto | way in | | |
| `research` | matt | auto | any time | | Write the notes where the project map puts research. |
| `wizard` | matt | auto | any time | | |
| `/handoff` | matt | typed | moving work elsewhere | | |

## Denied duplicates

Each one duplicates an `auto` skill above with different rules, so only the one above fires.

| Command | Source | Visibility | Duplicates |
|---|---|---|---|
| `engineering:architecture` | synced:engineering | denied | domain-modeling (ADRs) |
| `engineering:code-review` | synced:engineering | denied | code-review |
| `engineering:debug` | synced:engineering | denied | diagnosing-bugs |
| `engineering:testing-strategy` | synced:engineering | denied | tdd |
| `anthropic-skills:frontend-design` | synced:anthropic-skills | denied | frontend-design:frontend-design |
| `productivity:memory-management` | synced:productivity | denied | Claude Code's own memory |
