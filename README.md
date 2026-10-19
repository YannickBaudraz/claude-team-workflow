# Claude team workflow

My personal workflow for new projects with Claude Code, run the way an engineering team works: discovery, setup, roadmap, epics, refinement, tickets, test-first build, peer review, approval and a retro per epic.

`/ask-team` is the entry point. It reads where the project stands and prints the next command to run, in which session, and what has to be approved before moving on. It routes across my own skills, Matt Pocock's plugin and a set of community skills, each picked for the step it does best.

The whole workflow on one page: https://yannickbaudraz.github.io/claude-team-workflow/

## Contents

| Path | What it is |
|---|---|
| `skills/ask-team/` | The router: `SKILL.md`, `REGISTRY.md` (every skill the workflow names and how it is reached), `scripts/check-registry.py`, `templates/` |
| `skills/project-setup/` | Decides a project's tools and where each kind of document lives, writes the project map, places the conventions |
| `skills/change-request/` | The way in for a feature, improvement or bug fix in an existing project: diagnose or grill it, size it, write it as one issue |
| `skills/build-ticket/` | One ticket: branch, test-first build, pull request |
| `skills/epic-retro/` | Retrospective of a finished epic from the evidence it left |
| `install/community-skills.txt` | The community skills the workflow installs |
| `install/settings-fragment.json` | The settings it needs: command-only skills, blocked duplicates, Matt Pocock's marketplace |
| `install.sh` | Installs all of the above on a machine |
| `docs/build-workflow.py` | Builds the workflow page from the router's `SKILL.md` and `REGISTRY.md` |
| `docs/fonts/` | The page's fonts, served with it so no visitor's browser calls a third party |
| `.github/workflows/pages.yml` | Builds that page and publishes it to GitHub Pages on every push to `main` |

The community skills are installed from their authors' repositories, not copied here: their licences stay with them, and updates come from them.

## Install

Needs Claude Code (`claude`), Node.js for `npx`, `jq` and `python3`.

```bash
git clone https://github.com/YannickBaudraz/claude-team-workflow.git ~/Dev/claude-team-workflow
~/Dev/claude-team-workflow/install.sh
```

The script links this repo's skills into `~/.claude/skills`, so edits here are live. It shows the settings diff and asks before changing `~/.claude/settings.json`. Start a new Claude Code session afterwards.

## Maintenance

- After installing, removing or updating a skill the workflow uses, update `skills/ask-team/REGISTRY.md`, its Does line included (and `install/` when the list changes), then run `python3 ~/.claude/skills/ask-team/scripts/check-registry.py`.
- The workflow page follows `SKILL.md` and the registry on its own: every push to `main` rebuilds and publishes it. To preview it, run `python3 docs/build-workflow.py`, then `python3 -m http.server -d docs` and open http://localhost:8000/workflow.html (opened straight from disk, browsers block its fonts).
- Community skills: `npx skills update -g`. Matt Pocock's plugin updates itself from his marketplace.

## Credits

Built on skills from `mattpocock/skills`, `addyosmani/agent-skills`, `obra/superpowers`, `citypaul/.dotfiles`, `deanpeters/Product-Manager-Skills`, `product-on-purpose/pm-skills`, `riekelt/technical-writer`, `davidlee/doctrine` and `softaworks/agent-toolkit`. The router's shape follows Matt Pocock's `ask-matt`; the epic retro follows the structure of the BMAD Method's retrospective.

## Licence

MIT, see `LICENSE`. The fonts in `docs/fonts/` (Bricolage Grotesque, Instrument Sans and JetBrains Mono) are under the SIL Open Font License 1.1; each one's licence sits beside it.
