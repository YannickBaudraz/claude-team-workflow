---
name: project-setup
description: Set up a new project for the team workflow: decide its tools and where each kind of document lives, write the project map, and place the conventions.
disable-model-invocation: true
---

# Project setup

Runs after discovery (`/grill-with-docs`), before any planning. Its output is the **project map**: which tools the project uses and where each kind of document lives, read by agents and people alike. Templates live in `~/.claude/skills/ask-team/templates/`.

Placement is decided from this project's context, never from a default list. Some answers are obvious; many depend on the situation (a database shared by several apps, a domain owned by non-developers, a project small enough to keep everything in the repo).

## 1. Understand the context

Read what discovery produced: the conversation, the repo's `GLOSSARY.md` and ADRs if any. Then settle, in rounds of numbered questions each with your recommended answer, whatever discovery left open:

- How big is the project, and who works on it besides the user?
- Which issue tracker, documentation tool, code host and CI does it use, if any?
- Is the domain shared with other systems or repos, and does a domain doc already exist? Who owns it?
- Who reads which documents: developers only, or also people who never open the repo?

Done when every tool is named (or explicitly "none") and the user has confirmed the answers.

## 2. Decide where each kind of document lives

Fill the table in `templates/project-map.md` for every kind of document this project will produce, with a reason per row. Recommend the place, and let the user decide.

- The map itself goes in the **highest source of truth**: the documentation tool when the project has one above its repos, otherwise the repo.
- Every repo keeps its own `GLOSSARY.md`, limited to the domain knowledge its code uses. When a domain doc exists, it wins on meaning, and agents only read it.

Done when every row has a place and a reason, and the user has approved the table.

## 3. Write the map and the pointer

Write the map where step 2 put it. When it lives outside the repo, add the pointer from the template to the repo's `CLAUDE.md` or `AGENTS.md`, whichever exists; ask which to create when neither does. The pointer is the only line this step adds to that file.

Move anything discovery already wrote (glossary terms, ADRs) when the map puts it elsewhere.

## 4. Place the conventions

Copy each template where the map says, adapted to the project's stack and tools:

- `definition-of-done.md`.
- `coding-standards.md`, with the *Enforced by tools* table filled from the project's own lint, format, type-check and test commands.
- `pull-request-template.md`, at the code host's path: `.github/pull_request_template.md`, `.gitlab/merge_request_templates/Default.md` or `.gitea/pull_request_template.md`.

Done when each convention file exists where the map says and the user has seen the list.

## 5. Hand over

Tell the user to type `/setup-matt-pocock-skills` next, with the tracker from the map, and `/ci-cd-and-automation` once the project has code to build. Then point them to `/ask-team` for the next step.
