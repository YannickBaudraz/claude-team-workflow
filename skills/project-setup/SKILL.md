---
name: project-setup
description: Set up a project for the team workflow, new or existing: decide its tools and where each kind of document lives, write the project map, and place the conventions.
disable-model-invocation: true
---

# Project setup

Runs before any planning: after discovery (`/grill-with-docs`) for a new project, or when an **existing codebase** joins the workflow, where the repo itself is the context. Its output is the **project map**: which tools the project uses and where each kind of document lives, read by agents and people alike. Templates live in `~/.claude/skills/ask-team/templates/`.

Placement is decided from this project's context, never from a default list. Some answers are obvious; many depend on the situation (a database shared by several apps, a domain owned by non-developers, a project small enough to keep everything in the repo). What the repo already has outranks the templates: they fill gaps, they replace nothing.

## 1. Explore the repo

Read what exists before asking anything:

- the git history and the source tree: is this a new project or an existing codebase?
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, and any definition of done or coding standards under another name;
- the PR or merge request template at the code host's path;
- lint, format, type-check, test and build commands: `package.json` scripts, a `Makefile`, the CI workflow files;
- where documents already live: `docs/`, `docs/adr/`, `GLOSSARY.md`, a wiki the README links;
- the tracker: open issues, and the labels in use.

Decide from these whether the project is new or an existing codebase, and ask the user only when the signs conflict (history but no source, discovery in the conversation for a repo with years of commits).

Done when every item above is found or known to be absent.

## 2. Understand the context

For a new project, read what discovery produced: the conversation, the repo's `GLOSSARY.md` and ADRs if any. For an existing codebase, the exploration is the context. Then settle, in rounds of numbered questions each with your recommended answer, whatever is still open:

- How big is the project, and who works on it besides the user?
- Which issue tracker, documentation tool, code host and CI does it use, if any?
- Is the domain shared with other systems or repos, and does a domain doc already exist? Who owns it?
- Who reads which documents: developers only, or also people who never open the repo?

Done when every tool is named (or explicitly "none") and the user has confirmed the answers.

## 3. Decide where each kind of document lives

Fill the table in `templates/project-map.md` for every kind of document this project will produce, with a reason per row. Recommend the place, and let the user decide.

- Where the repo already keeps a kind of document, propose that place. The template's suggestion only fills a kind the repo has nowhere for.
- For a kind the repo has nowhere for, propose the project's own tool for it first: its documentation tool, project management tool or tracker. The repo is the place when the project has no such tool, or for what agents read with the code, such as the glossary and the coding standards.
- The Interface designs and Visual direction rows are for a product with a user interface; for one without, they read "none: no user interface".
- The map itself goes in the **highest source of truth**: the documentation tool when the project has one above its repos, otherwise the repo.
- Every repo keeps its own `GLOSSARY.md`, limited to the domain knowledge its code uses. When a domain doc exists, it wins on meaning, and agents only read it. A new glossary starts empty: `domain-modeling` fills it as terms come up.
- For an existing codebase with no problem statement or roadmap, the Roadmap row reads "none; planned at step 4 when wanted". The router reads that row, so planning stays a choice rather than the next step.

Done when every row has a place and a reason, and the user has approved the table.

## 4. Write the map and the pointer

Write the map where step 3 put it. When it lives outside the repo, add the pointer from the template to the repo's `CLAUDE.md` or `AGENTS.md`, whichever exists; ask which to create when neither does. The pointer is the only line this step adds to that file.

Move anything discovery already wrote (glossary terms, ADRs) when the map puts it elsewhere.

## 5. Place the conventions

For each convention, the repo's own file wins when it has one: the map points at it, and you add only what the workflow needs from the template, showing each added line to the user for approval. When the repo has none, copy the template where the map says, adapted to the project's stack and tools:

- the definition of done, from `definition-of-done.md`;
- the coding standards, from `coding-standards.md`. The *Enforced by tools* table comes from the commands step 1 found. The judgement calls come from the repo's own guide when it has one; otherwise the section stays empty for retros to grow;
- the PR template, from `pull-request-template.md`, at the code host's path: `.github/pull_request_template.md`, `.gitlab/merge_request_templates/Default.md` or `.gitea/pull_request_template.md`. The workflow needs its ticket link and its definition-of-done checklist.

Done when each convention exists where the map says, every added line was approved, and the user has seen the list.

## 6. Guard the merge

In this project the merge is the user's act. The settings keep the agent from merging a PR, pushing to the default branch or changing a branch rule: a filter against mistakes, not a lock, since the agent works under the user's own login.

- Merge `templates/claude-settings.json` into the repo's `.claude/settings.json`, creating it when absent: keep its other keys, add each deny rule it lacks, and add the hook entry once. Copy `~/.claude/skills/ask-team/hooks/merge-guard.py` to `.claude/hooks/merge-guard.py`. Show the user the diff before writing. A global gitignore may ignore `.claude`: run `git check-ignore -v` on both files, add them with `git add -f` when ignored, and tell the user. Both are committed, so every local session and every single-repository cloud session on this repo carries them; a cloud thread of a Claude project or a cloud session on several repositories does not (FLOW.md, Sessions).
- Write the commands the user runs themselves, in a terminal or in shell mode (`!`); the guard refuses them to the agent:
  1. for a new repository whose default branch is not on the remote yet, its first push: `git push -u origin <default branch>`, with setup's files committed on that branch. It comes before any other push, or the code host may take the first branch pushed as the default. The agent may create the remote, without `--push`;
  2. where the code host offers one, the branch rule on the default branch: changes only through a pull request, with no approval required, no force push, no deletion, and no one allowed to bypass it. On GitHub:

     ```bash
     gh api -X POST repos/<owner>/<repo>/rulesets --input - <<'EOF'
     {"name": "Default branch", "target": "branch", "enforcement": "active", "bypass_actors": [],
      "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
      "rules": [{"type": "deletion"}, {"type": "non_fast_forward"},
                {"type": "pull_request", "parameters": {"required_approving_review_count": 0,
                 "dismiss_stale_reviews_on_push": false, "require_code_owner_review": false,
                 "require_last_push_approval": false, "required_review_thread_resolution": false}}]}
     EOF
     ```

     On another host, name its equivalent setting. The rule requires no CI status yet. When the project's CI check later becomes required on it, that check runs on every PR, with no path filter, and holds the project's other checks inside it, so a PR it never reports on is never blocked.

In an existing codebase, whose default branch is already on the remote, setup's files reach it like any change: committed on a setup branch and opened as one PR, which the user merges. The branch rule can be set before or after that merge.

Once the default branch is on the remote, run `git remote set-head origin --auto`, so the guard knows it. When it is named neither main nor master, add to the deny rules the four `git push` rules of main with its name.

Done when `git ls-files` lists both files, the user approved them, and the user has the commands.

## 7. Hand over

Tell the user to type `/setup-matt-pocock-skills` next, with the tracker and the labels from the map; when the tracker already has open issues, add one line to the tracker doc it writes: issues opened before today's date have not been triaged. Add one more line to it: a document is approved when it ends with `Approved by <name> on <date>`, written when the user approves it. Name `/ci-cd-and-automation` only when the repo has no CI and has code to build.

When `/change-request` sent the user here, the change continues in this session. Otherwise point them to `/ask-team` for the next step.
