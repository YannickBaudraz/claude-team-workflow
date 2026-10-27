# Project map: <project name>

Where this project's work and knowledge live, for the people and the agents working on it. This page is the source of truth for placement; when another document disagrees about where something lives, this page wins.

## Tools

| Tool | What we use | Where | How agents reach it |
|---|---|---|---|
| Issue tracker | <Jira / GitHub Issues / GitLab / local markdown / none> | <project URL or folder> | <MCP server, CLI, or files> |
| Documentation | <Confluence / Notion / Google Drive / the repo> | <space or folder URL> | <MCP server, or files> |
| Code host | <GitHub / GitLab / Gitea> | <repo URL> | <gh / glab / tea> |
| CI | <GitHub Actions / GitLab CI / Gitea Actions / none> | <pipeline URL> | <CLI> |
| Design | <Figma / none> | <file URL> | <MCP server> |

## Where each kind of document lives

One row per kind of document this project produces. When a new kind appears, decide its place and add a row before writing the first one.

| Kind | Lives in | Link | Owner | Why there |
|---|---|---|---|---|
| Domain doc (shared knowledge across systems) | | | | |
| Glossary for this repo's code | repo: `GLOSSARY.md` | | developers | Every agent session reads it. |
| Problem statement and solution brief | | | | |
| Roadmap | | | | |
| PRDs | | | | |
| Interface designs | | | | |
| Visual direction | | | | |
| Design docs | | | | |
| ADRs | | | | |
| Epics, stories and tickets | issue tracker | | | |
| Definition of done | | | | |
| Coding standards | repo: `CODING_STANDARDS.md` | | developers | The reviewer reads it with the diff. |
| Research notes | | | | |
| Retros | | | | |

## Domain

When a domain doc exists, it is the source of truth for the domain and its owner decides its content. This repo's glossary narrows it to the terms the code uses. A disagreement between the two becomes a question to the domain doc's owner, never an edit on either side.

## Pointer for the repo

Put this in the repo's `CLAUDE.md` (or `AGENTS.md`), whichever exists, when this map lives outside the repo:

```markdown
## Project map

Tools, and where each kind of document lives: <link to this map>.
```
