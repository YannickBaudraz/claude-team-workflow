# Project map: Pantry

## Tools

| Tool | What we use | Where | How agents reach it |
|---|---|---|---|
| Issue tracker | local markdown | `issues/` | files, see `docs/agents/issue-tracker.md` |
| Documentation | the repo | `docs/` | files |
| Code host | GitHub | not pushed yet | gh |
| CI | none | | |
| Design | none | | |

## Project facts

| Fact | Value | Why | Confirmed |
|---|---|---|---|
| Interface | graphical | Pantry is a web page with a form. | 2026-10-01 |
| Deploy target | none | It runs on the developer's laptop. | 2026-10-01 |
| Users | the developer only; made for home cooks, who can be reached among friends | A tool for the developer's own kitchen first. | 2026-10-01 |
| Model-driven features | none | | 2026-10-01 |
| Kind | personal | | 2026-10-01 |
| Exposure | local only | | 2026-10-01 |
| Data | no personal data | It stores food items only. | 2026-10-01 |

## Where each kind of document lives

| Kind | Lives in | Link | Owner | Why there |
|---|---|---|---|---|
| Domain doc (shared knowledge across systems) | none: the domain is this tool's alone | | | Nothing outside the repo shares it. |
| Glossary for this repo's code | repo: `GLOSSARY.md` | | developers | Every agent session reads it. |
| Problem statement and solution brief | repo: `docs/product/` | | product owner | Small project, one repo. |
| Roadmap | story map: `docs/product/story-map.md`; epics: issue tracker, one per release slice | | product owner | The map shapes the slices; the tracker holds the epics. |
| PRDs | repo: `docs/prd/<epic>.md` | | product owner | |
| Interface designs | repo: `docs/interface/<epic>.md` | | interface designer | Next to the code the screens live in. |
| Visual direction | repo: `docs/interface/visual-direction.md` | | interface designer | One for the product. |
| Design docs | repo: `docs/design/<epic>.md` | | architect | Next to the code they describe. |
| ADRs | repo: `docs/adr/` | | architect | |
| Epics, stories and tickets | issue tracker: `issues/` | | everyone | |
| Definition of done | repo: `docs/definition-of-done.md` | | developers | |
| Coding standards | repo: `CODING_STANDARDS.md` | | developers | The reviewer reads it with the diff. |
| Research notes | repo: `docs/research/` | | | |
| Retros | repo: `docs/retros/` | | | |
