# Project map: Pantry

## Tools

| Tool | What we use | Where | How agents reach it |
|---|---|---|---|
| Issue tracker | local markdown | `issues/` | files, see `docs/agents/issue-tracker.md` |
| Documentation | the repo | `docs/` | files |
| Code host | GitHub | not pushed yet | gh |
| CI | none | | |
| Design | none | | |

## Where each kind of document lives

| Kind | Lives in | Link | Owner | Why there |
|---|---|---|---|---|
| Domain doc (shared knowledge across systems) | none: the domain is this tool's alone | | | Nothing outside the repo shares it. |
| Glossary for this repo's code | repo: `GLOSSARY.md` | | developers | Every agent session reads it. |
| Problem statement and solution brief | repo: `docs/product/` | | product | Small project, one repo. |
| Roadmap | story map: `docs/product/story-map.md`; epics: issue tracker, one per release slice | | product | The map shapes the slices; the tracker holds the epics. |
| Design docs | repo: `docs/design/<epic>.md` | | tech lead | Next to the code they describe. |
| ADRs | repo: `docs/adr/` | | tech lead | |
| PRDs | repo: `docs/prd/<epic>.md` | | product | |
| Epics, stories and tickets | issue tracker: `issues/` | | everyone | |
| Definition of done | repo: `docs/definition-of-done.md` | | developers | |
| Coding standards | repo: `CODING_STANDARDS.md` | | developers | The reviewer reads it with the diff. |
| Research notes | repo: `docs/research/` | | | |
| Retros | repo: `docs/retros/` | | | |
