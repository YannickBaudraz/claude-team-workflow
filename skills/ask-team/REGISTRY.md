# Registry

Every skill the team workflow names, and how it is reached. `scripts/check-registry.py` reads the tables below, so keep their columns.

**Source** is the repository the skill comes from (`Claude Code` for a built-in one). The check finds the installed skill from it: a plugin from the marketplace hosted in that repo, a synced Anthropic plugin or skill, or `~/.claude/skills`, where this repo's skills are links and community skills must match `install/community-skills.txt`.

**Visibility** says who can start the skill:

- `typed`: command-only by its own frontmatter; only the user starts it.
- `hidden`: command-only through `skillOverrides: "user-invocable-only"` in `~/.claude/settings.json`; only the user starts it.
- `auto`: Claude may load it on its own, and other skills may call it.
- `denied`: blocked for Claude by `permissions.deny`; the user can still type it.
- `built-in`: ships with Claude Code.

A skill may only **call** an `auto` or `built-in` skill: Claude Code refuses a call to a `typed` or `hidden` one. `file:` marks a skill read directly from disk, which works whatever its visibility.

**Does** says what the skill does, in one line; the workflow page shows it.

**Used at** starts with the step number when the skill belongs to a step; otherwise it says `entry point`, `way in` or `any time`, or when the skill is used outside the flow. The workflow page groups skills by it.

**Arguments** are appended to the command when the router prints it, so the skill follows this workflow's conventions instead of its own defaults. The project map is the per-project document that says which tools the project uses and where each kind of document lives; the tracker doc is `docs/agents/issue-tracker.md`.

## Workflow skills

| Command | Source | Visibility | Used at | Calls | Arguments | Does |
|---|---|---|---|---|---|---|
| `/ask-team` | `YannickBaudraz/claude-team-workflow` | typed | entry point, any time |  |  | Reads where the project stands and prints the next command, the session to run it in, and what you must approve first. It never runs the step. |
| `/project-setup` | `YannickBaudraz/claude-team-workflow` | typed | 2 Setup |  |  | Decides the project's tools and where each kind of document lives, writes the project map, and places the definition of done, PR template and coding standards. |
| `/build-ticket` | `YannickBaudraz/claude-team-workflow` | typed | 10 Build | file:incremental-implementation, file:test-driven-development, file:finishing-a-development-branch | `<ticket id>` | Builds one ticket test-first on its own branch and opens a pull request with the template filled. |
| `/epic-retro` | `YannickBaudraz/claude-team-workflow` | typed | 13 Retro | lesson-learned | `<epic id>` | The retrospective of a finished epic from the evidence it left: sourced findings, a verdict against its goals, action items. |
| `/grill-with-docs` | `mattpocock/skills` | typed | 1 Discovery | grilling, domain-modeling | Read the domain doc first if the project map names one. | A relentless interview that sharpens an idea and writes glossary terms and ADRs as it goes. |
| `/grill-me` | `mattpocock/skills` | typed | 1 Discovery, before any folder | grilling |  | The same interview without docs. |
| `grilling` | `mattpocock/skills` | auto | 1 Discovery, under grill-with-docs, triage, wayfinder |  |  | The questioning loop behind the grill commands, /triage and /wayfinder. |
| `domain-modeling` | `mattpocock/skills` | auto | glossary terms and ADRs, any time |  | The domain doc wins over the repo glossary on meaning; raise a disagreement with its owner. | Settles a contested term in GLOSSARY.md or records an ADR. |
| `/setup-matt-pocock-skills` | `mattpocock/skills` | typed | 2 Setup |  | Tracker, labels and glossary layout as the project map says. | Points Matt Pocock's skills at the project's tracker, triage labels and glossary layout. |
| `/wayfinder` | `mattpocock/skills` | typed | 3 Fog | grilling, domain-modeling, prototype, research | When the map clears, continue at step 4, not /to-spec. | Plans an effort too big for one session as a map of decision tickets on the tracker, then resolves them one at a time. |
| `/define-problem-statement` | `product-on-purpose/pm-skills` | hidden | 4 Problem |  | Save where the project map puts the problem statement. | Frames the problem: who it affects, the business context, and how success is measured. |
| `/develop-solution-brief` | `product-on-purpose/pm-skills` | hidden | 4 Brief |  | Save where the project map puts the solution brief. | A one-page overview of the proposed approach, its key decisions and trade-offs. |
| `/user-story-mapping-workshop` | `deanpeters/Product-Manager-Skills` | hidden | 5 Roadmap | file:workshop-facilitation, file:user-story-mapping | Each release slice becomes one epic. Stop at the map; stories are refined at step 8. | A guided workshop that builds the story map: backbone activities, tasks and release slices. |
| `workshop-facilitation` | `deanpeters/Product-Manager-Skills` | auto | 5 Roadmap, under the workshop |  |  | Paces a workshop one step at a time, with options and progress. |
| `/user-story-mapping` | `deanpeters/Product-Manager-Skills` | hidden | 5 Roadmap, read by the workshop |  |  | The story map format: activities, steps, tasks and release slices. |
| `/technical-writing` | `riekelt/technical-writer` | hidden | 6 Design |  | Use it as the writing style only; leave CLAUDE.md unchanged. | The house style for technical prose: truth and sourcing rules, banned constructions. |
| `/writing-design-docs` | `riekelt/technical-writer` | hidden | 6 Design |  | Run after /technical-writing in the same session. Record decisions as ADRs with domain-modeling. Save where the project map puts design docs. | The design doc skeleton, its Why & What decision box and completeness checks. |
| `prototype` | `mattpocock/skills` | auto | 6 Design |  |  | A throwaway prototype that answers one design question with running code. |
| `frontend-design:frontend-design` | `anthropics/claude-plugins-official` | auto | 6 Design, UI only |  |  | Visual direction for UI work: aesthetic, typography, choices that don't look templated. |
| `/deliver-prd` | `product-on-purpose/pm-skills` | hidden | 7 PRD |  | `<epic>`. Save in the epic's home from the project map. About 7 user stories, never more than 9; detail goes into requirements and acceptance criteria. | A PRD: what to build, why, and how success is measured. |
| `/specification` | `citypaul/.dotfiles` | hidden | 8 Refinement |  | `<story>`. The story lives in the tracker. Open decisions go to /grill-with-docs; new terms to domain-modeling. | Turns a story into agreed rules, examples and acceptance criteria, one question at a time. |
| `/story-splitting` | `citypaul/.dotfiles` | hidden | 8 Refinement |  | Hand the chosen slices to /to-tickets. | Splits a story that is too big into small end-to-end slices, never into technical tasks. |
| `/find-gaps` | `citypaul/.dotfiles` | hidden | 8 Refinement |  | Write the closed gaps back into the story in the tracker. | An adversarial pass over a written story or plan: missing states, edge cases, unstated assumptions, criteria no one can check. |
| `/to-tickets` | `mattpocock/skills` | typed | 9 Tickets |  | `<epic or story>`. Tickets the user will build themselves get `ready-for-human`. | Breaks a plan into tracer-bullet tickets with blocking edges and publishes them to the tracker. |
| `/pair` | `davidlee/doctrine` | hidden | 10 Build, pairing |  | `role=… detail=… autonomy=…` | Pair programming with you in the loop, set by three dials: role, detail and autonomy. |
| `test-driven-development` | `addyosmani/agent-skills` | hidden | 10 Build, read by /build-ticket |  |  | The red-green-refactor loop. |
| `incremental-implementation` | `addyosmani/agent-skills` | hidden | 10 Build, read by /build-ticket |  |  | Thin slices, each one verified before the next. |
| `finishing-a-development-branch` | `obra/superpowers` | hidden | 10 Build, read by /build-ticket |  |  | Final checks and the options for integrating the branch. |
| `tdd` | `mattpocock/skills` | auto | ad-hoc test-first work | codebase-design |  | Test-first work with red-green-refactor and integration tests. |
| `codebase-design` | `mattpocock/skills` | auto | any time |  |  | Shared vocabulary for deep modules: interfaces, seams, testability. |
| `pr` | `mattpocock/skills` | auto | 10 Build, PR bodies |  |  | Writes pull request bodies. |
| `/code-review-and-quality` | `addyosmani/agent-skills` | hidden | 11 Review |  | `<PR>`. Against the ticket's acceptance criteria and CODING_STANDARDS.md. Post the findings on the PR. | A multi-axis review of a change before it merges. |
| `code-review` | `mattpocock/skills` | auto | ad-hoc reviews |  |  | Reviews changes since a fixed point against the repo's coding standards and the originating spec. |
| `/security-review` | Claude Code | built-in | 11 Review |  |  | Claude Code's built-in security review of the pending changes. |
| `receiving-code-review` | `obra/superpowers` | auto | 11 Review, acting on feedback |  |  | How to act on review feedback: check each point before changing code, never agree blindly. |
| `/plannotator-review` | `backnotprop/plannotator` | typed | 11 Review, the user reviews |  | `<PR or worktree>` | Opens the diff in your browser to annotate; Claude then works through your notes. |
| `/acceptance-review` | `citypaul/.dotfiles` | hidden | 12 Approval |  | `<PR> against <ticket>`. The ticket is the authoritative contract. | A read-only, criterion-by-criterion proof that a PR meets its ticket or spec. |
| `/ci-cd-and-automation` | `addyosmani/agent-skills` | hidden | 2 Setup, once per project |  | For the code host in the project map. Show each commit and wait for approval. | Sets up CI and its quality gates. |
| `/retro` | `mattpocock/skills` | typed | 13 Retro | writing-for-agents | The sessions of the epic just closed. | Reviews coding sessions and suggests changes to Claude's setup: navigation pointers, automated checks, coding standards. |
| `writing-for-agents` | `mattpocock/skills` | auto | 13 Retro, under /retro; editing skills or CLAUDE.md |  |  | The writing style for skills, AGENTS.md and CLAUDE.md. |
| `lesson-learned` | `softaworks/agent-toolkit` | auto | 13 Retro, any time |  |  | Pulls engineering lessons out of recent git history. |
| `/triage` | `mattpocock/skills` | typed | way in | grilling, domain-modeling |  | Moves incoming issues and outside PRs through triage states, grills where needed and writes agent-ready briefs. |
| `diagnosing-bugs` | `mattpocock/skills` | auto | way in |  |  | A diagnosis loop for hard bugs and performance regressions. |
| `engineering:incident-response` | `anthropics/knowledge-work-plugins` | auto | way in |  |  | Production incident: triage, status updates and a blameless postmortem. |
| `research` | `mattpocock/skills` | auto | any time |  | Write the notes where the project map puts research. | A cited write-up from primary sources, saved in the repo. |
| `wizard` | `mattpocock/skills` | auto | any time |  |  | Generates an interactive script that walks you through steps only you can take, such as credentials or a dashboard. |
| `/handoff` | `mattpocock/skills` | typed | any time, moving work elsewhere |  |  | Writes a handoff document so another agent or person can pick up the work. |
| `/suggest-title` | `YannickBaudraz/claude-team-workflow` | typed | any time, naming a session |  |  | Proposes a name for the current session that you will recognise in /resume, distinct from the project's other session names, with the /rename line to paste. |

## Denied duplicates

Each one duplicates an `auto` skill above with different rules, so only the one above fires.

| Command | Source | Visibility | Duplicates |
|---|---|---|---|
| `engineering:architecture` | `anthropics/knowledge-work-plugins` | denied | domain-modeling (ADRs) |
| `engineering:code-review` | `anthropics/knowledge-work-plugins` | denied | code-review |
| `engineering:debug` | `anthropics/knowledge-work-plugins` | denied | diagnosing-bugs |
| `engineering:testing-strategy` | `anthropics/knowledge-work-plugins` | denied | tdd |
| `anthropic-skills:frontend-design` | `anthropics/skills` | denied | frontend-design:frontend-design |
| `productivity:memory-management` | `anthropics/knowledge-work-plugins` | denied | Claude Code's own memory |
