# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Me, first.** I run new and existing projects with Claude Code through this workflow and use the page as my own reference while working: where a project stands, which step comes next, which session runs it, what has to be approved before moving on.
- **People looking at how I work.** Peers, recruiters or clients who open the repo or the page to see how I run a project with Claude Code. Other developers are welcome to install it, but the page is not built to sell it to them.

## Product Purpose

A personal workflow for new and existing projects with Claude Code, run the way an engineering team works: discovery, setup, roadmap, epics, refinement, tickets, test-first build, review, approval and a retro per epic. `/ask-team` is the entry point: it reads the project's state and prints the next command to paste, the session to run it in, and the gate before the step after it.

The workflow page (https://yannickbaudraz.github.io/claude-team-workflow/) shows the whole workflow on one page. Someone who opens it succeeds when they:

- know the next step for a project at a glance;
- understand the full cycle from idea to retro, gates and sessions included;
- come away trusting that the workflow is rigorous and well made.

## Positioning

A router, not a skill pack: `/ask-team` never runs a step itself, it prints the next command. It routes across my own skills, Matt Pocock's plugin and a curated set of community skills, each picked for the step it does best and named with its real source in the registry. The workflow is shaped on how a real team works, with approval gates that stay the user's and sessions split by role (product owner, interface designer, architect, developer, reviewer).

## Operating Context

- Used inside Claude Code sessions, one session per role; the page is read beside the terminal.
- Requests are sized before routing: a spike, a bounded change (one ticket), or an architectural change or new product (the main flow).
- Installed with `install.sh`, which links the repo's skills into `~/.claude/skills` and asks before changing `~/.claude/settings.json`.

## Capabilities and Constraints

- The page is generated: `docs/build-workflow.py` builds it from `skills/ask-team/SKILL.md` and `skills/ask-team/REGISTRY.md`. Content changes go in those two files, never in the page. `docs/build-workflow.py` is only the command line; the code that makes the page is in `docs/workflow/`, where `config.py` holds the page's own frame (title, lede, short glossary).
- Published to GitHub Pages by `.github/workflows/pages.yml` on every push to `main`. `docs/workflow.html` is a gitignored build output.
- No visitor's browser calls a third party: fonts are self-hosted from `docs/fonts/` under the SIL Open Font License, licences beside them.
- Light and dark themes both supported, in five palettes (Reader, the page's own; Cool; Catppuccin; Tokyo Night; Nord): the page follows the system in Reader unless the visitor picks a mode or a palette in the bar's appearance menu, which it remembers. Every palette keeps its text at 4.5:1 or better; the build checks it.
- English only.
- Terminology from the sources: epic, PRD, ADR, spike, Fog, tracer-bullet ticket, blocking edge, CI green, frontier.

## Brand Commitments

- Name: Claude Team Workflow. Lede: "From an idea to a merged epic, run the way an engineering team works."
- Voice: first person on the repo ("my personal workflow"); the page turns the router's "the user" into "you". Plain, exact, no marketing.
- Credits to the skills' authors stay visible; community skills are installed from their authors' repositories, not copied.

## Evidence on Hand

- The router (`skills/ask-team/SKILL.md`), the registry (`skills/ask-team/REGISTRY.md`), the templates, `install.sh`, the MIT licence.
- No testimonials, adoption numbers or user counts exist. Do not invent any.

## Product Principles

1. The sources are the truth: the page follows `SKILL.md` and the registry, never the other way round.
2. Always end on the next command: whatever is shown, the reader should be able to tell what to run next and where.
3. Gates belong to the human: nothing is shown as approved because its output exists.
4. Credit and provenance are part of the product: every skill names where it comes from.
5. Rigour shows in the details, not in claims.
