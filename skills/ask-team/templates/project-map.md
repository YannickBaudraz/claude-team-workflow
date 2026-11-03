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

## Project facts

The facts that differ between projects and decide which steps run. Each row has its reason and the date it was last confirmed: setup fills them, and each epic retro confirms them again. A fact that changed sends the work it turns on through `/change-request`.

| Fact | Value | Why | Confirmed |
|---|---|---|---|
| Interface | <graphical / command line or API only / none> | | <date> |
| Deploy target | <its name / none> | | <date> |
| Users | <none yet / the developer only / others>; made for <who the product is for>, who <can / cannot> be reached | | <date> |
| Model-driven features | <yes / none> | | <date> |
| Kind | <personal / client / sold> | | <date> |
| Exposure | <local only / known people, such as a client's staff / public internet> | | <date> |
| Data | <no personal data / ordinary personal data / sensitive data, money or credentials> | | <date> |

## Client

Only for a project whose kind is client; delete this section otherwise. When the map lives in a public repo, this section names roles only: the client's names and account details stay in the documentation tool or another private place, which the section links.

| For the client | What, or who |
|---|---|
| Approver | <name and role> |
| Where the client reads | <published copies of the repo's documents / a shared documentation tool>. The client reads rendered artefacts: clickable wireframes, shots, a preview or staging link. Internal notes stay apart. |
| Brand guidelines and accessibility obligations | <links, or none> |
| Acceptance terms | <the window, the criteria and who signs>; copied into the definition of done |
| Security and privacy obligations | <from the contract, or none> |
| Accounts and secrets | <who owns each>. The client's own accounts are used where possible. |
| At handover | <the documents the client keeps, and where>; every access to the client's accounts and data is removed |

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
