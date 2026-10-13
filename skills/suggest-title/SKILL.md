---
name: suggest-title
description: Propose a name for the current session that you will recognise later in /resume, distinct from the project's other session names, with the /rename line to paste. Workflow sessions get the step and the item; any other session gets its subject.
argument-hint: "[list | workflow | general] [hint]"
disable-model-invocation: true
---

# Suggest title

The user resumes sessions from a list of names. Generated titles fail them two ways: they describe the last few messages instead of the session ("rename-session-commands" for a session that mostly redesigned a page), and they repeat ("Sequential test run" three times in one project). Propose one name they will recognise weeks later, among the names already in that list.

Built-in commands are the user's to type: never try to run `/rename`. Hand them the line.

## Arguments

The arguments, if any, are: `$ARGUMENTS`. They may start with one keyword, and anything after it is a hint:

- `list`: print the project's session names (step 1) and stop. Point out the duplicates and the generated ones, and offer to name this session.
- `workflow` or `general`: use that style even if step 2 would choose the other.
- A hint, alone or after the keyword: words the user wants in the name, or the part of the session to name it after. Follow it unless it makes the name a duplicate; then say so and add what tells them apart.

## 1. Read the names already taken

Run `python3 <this skill's directory>/scripts/session_titles.py`. It prints this project's sessions, newest first, flagged "this session", "duplicate" and "generated". A name too close to one of these is the problem the user is trying to escape. When it prints nothing, Claude Code keeps sessions differently than the script expects: carry on without comparing, and say so in one line.

## 2. Choose the style

Look back over the whole session, not the latest exchange. After a compaction, the summary at the top counts as much as what follows it.

It is a **workflow session** when its main work ran the team workflow's steps: the commands of the Main flow table in `~/.claude/skills/ask-team/SKILL.md`, which the session invoked or was sent to by `/ask-team`. Read that table only in that case, for the step names. Everything else is **general**: a session that only asked `/ask-team` what comes next, a way in (`/triage`, a diagnosis, an incident), an any-time or ad-hoc skill, or work outside any project the workflow runs.

## 3. Build the name

Both styles: lowercase ASCII words joined by hyphens. Length is free: a long name that tells the user which session this is beats a short one they have to open to check, so let it run as long as each word helps them choose. Use the words the user would search their memory for: the feature, the file, the tool, the symptom, the decision. Leave out words every session could carry (session, conversation, chat, task, help, work, update, fix alone, misc, clear).

**Workflow style**: `<step>-<subject>-<id>`.

- The step comes from the Main flow table: discovery, setup, fog, problem-brief, roadmap, design, prd, refinement, tickets, build, review, approval, retro.
- Several steps in one session: the first and the last, `design-to-tickets-...`.
- The subject is two or three words from the item's own title as the session saw it (the epic, story, ticket or PR), because the user will not remember IDs. Never invent one; without a title, use what the session built or decided.
- The ID goes last when the session showed it (`epic-3`, `PROJ-42`, `pr-118`), so the name stays exact.
- When another session already did this step on this item, add what this one did differently (`build-login-form-review-fixes-PROJ-42`).

**General style**: `<subject>-<what was done>`. When the session changed course, name each main thread in the order it happened, joined by `then` (`impeccable-critique-of-workflow-page-then-suggest-title-skill`): the user remembers a session by its arc, and the last thread alone would mislabel it.

**Lasting**: a theme comes back ("workflow page", "auth", "tests"), so a name made of the theme alone will collide with next week's session on it. Anchor the name on what only this session produced or settled: the artifact it built, the decision it took, the bug it closed. Put the theme second, or leave it out when the anchor already implies it. Ask yourself whether a later session on the same theme would plausibly earn the same name; if so, the anchor is too vague.

**Distinct**: compare with step 1. When the name shares its main words with another, change the words that would tell the user which one to open: the item, the outcome, the tool. Add `-2` only when nothing else differs.

## 4. Answer

Three names: your pick, and two alternatives that take another angle (the outcome instead of the subject, or another thread first), not a reshuffle of the same words.

Copy the recommended command first, with `sh <this skill's directory>/scripts/copy.sh "/rename <name>"`, so the likeliest answer is already on the clipboard. Write no text before the question: the question replaces it on screen.

Ask with the question tool (AskUserQuestion): "Which name for this session?", the three names as options, the first labelled "<name> (Recommended)", each description one line on what the name points to. The user may also type their own. When they choose another name, copy its `/rename` line instead.

Then end with this block, the chosen name first and the two others after `Also:`:

```
/rename <chosen name>
```
Also:
- `<other name>`
- `<other name>`

<one line: what the chosen name points to, and which existing name it avoids, if any>
Copied to the clipboard: paste it to rename the session.

When the copy fails (the script says no clipboard tool was found), replace the last line with that, so the user copies the line by hand. When the question tool is not available, skip the question and end with the same block for your pick.
