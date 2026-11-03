# Project map: claude-team-workflow

Where this project's work and knowledge live, for the people and the agents working on it. This page is the source of truth for placement; when another document disagrees about where something lives, this page wins.

## Tools

| Tool | What we use | Where | How agents reach it |
|---|---|---|---|
| Issue tracker | GitHub Issues | https://github.com/YannickBaudraz/claude-team-workflow/issues | `gh` |
| Documentation | the repo | https://github.com/YannickBaudraz/claude-team-workflow | files |
| Code host | GitHub | https://github.com/YannickBaudraz/claude-team-workflow | `gh` |
| CI | GitHub Actions | https://github.com/YannickBaudraz/claude-team-workflow/actions | `gh run` |
| Design | none | | |

## Where each kind of document lives

One row per kind of document this project produces. When a new kind appears, decide its place and add a row before writing the first one.

| Kind | Lives in | Link | Owner | Why there |
|---|---|---|---|---|
| Domain doc (shared knowledge across systems) | none | | | The workflow shares its domain with no other system. |
| Glossary for this repo's code | repo: `GLOSSARY.md` | [GLOSSARY.md](../GLOSSARY.md) | developers | Every agent session reads it. |
| Problem statement and solution brief | none: `README.md` and `PRODUCT.md` state the purpose | [README.md](../README.md), [PRODUCT.md](../PRODUCT.md) | Yannick | An existing codebase whose purpose is already written down. |
| Roadmap | none; planned at step 4 when wanted | | Yannick | The workflow decision issues carry the planned work. |
| Workflow decisions | issue tracker, labelled `decision`, `premortem-fix` or `rule`, plus an area | [decisions](https://github.com/YannickBaudraz/claude-team-workflow/issues?q=label%3Adecision) | Yannick | One issue per decision, titled with its id, so each PR links the decisions it carries. |
| PRDs | issue tracker, on the epic | | Yannick | The tracker is the project's own tool for planned work. |
| Interface designs | repo: `docs/interface/` | | Yannick | The workflow page is the interface, and it is built from the repo. |
| Visual direction | repo: `DESIGN.md`, with `PRODUCT.md` | [PRODUCT.md](../PRODUCT.md) | Yannick | Where the page's design skill reads and writes it. |
| Design docs | repo: `docs/design/` | | developers | Build sessions read them with the code. |
| ADRs | repo: `docs/adr/` | | developers | Read with the code they explain. |
| Epics, stories and tickets | issue tracker | [issues](https://github.com/YannickBaudraz/claude-team-workflow/issues) | Yannick | The tracker item is the hand-off between sessions. |
| Definition of done | repo: `docs/agents/definition-of-done.md` | [definition-of-done.md](agents/definition-of-done.md) | developers | Beside the tracker doc, read by every build and review. |
| Coding standards | repo: `CODING_STANDARDS.md` | [CODING_STANDARDS.md](../CODING_STANDARDS.md) | developers | The reviewer reads it with the diff. |
| Research notes | local: `.claude/research/`, ignored by git | | Yannick | They quote material that is not public. |
| Retros | issue tracker, a comment on the closed epic | | Yannick | Next to the epic they look back on. |

## Domain

When a domain doc exists, it is the source of truth for the domain and its owner decides its content. This repo's glossary narrows it to the terms the code uses. A disagreement between the two becomes a question to the domain doc's owner, never an edit on either side.
