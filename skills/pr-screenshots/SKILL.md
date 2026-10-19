---
name: pr-screenshots
description: Before and after screenshots in a pull request body, attached with gh. Use when opening or updating a PR that changes what a user sees: layout, styles, copy, a rendered page or component.
---

# PR screenshots

Reviewers judge a visible change from the PR body, without checking out the branch. Give them **pairs**: the same state rendered from the base branch and from the PR branch, with the same viewport, scroll and stored settings, so the only difference is the change.

## 1. Choose the states

List each page, component or state the diff changes: an open menu, an error, a grouping. For each, take desktop (1280 wide) and phone (390 wide), and light and dark when the project has both. Drop a combination the change cannot reach.

**Done when** every visible change in the diff maps to at least one state.

## 2. Find how the project renders

Take the first that exists:

1. A project skill that screenshots or runs the app; its description says so.
2. The run command in the project map or README.
3. The `run` skill.

Use its screenshot command when it has one. Otherwise use Playwright: `npx playwright screenshot --viewport-size=1280,900 [--color-scheme=dark] [--full-page] <url> <file>.png`. When Playwright is not installed, stop and tell the user: installing it is their call. Browsers run outside the Claude Code sandbox.

## 3. Render both sides

The **before** comes from the base branch: the PR's base, which in a stack is the branch below it. Check it out with `git worktree add --detach <tmp>/base <base>` and render it there. A before rebuilt from memory or by undoing edits is a guess, not a pair.

The **after** comes from the PR branch, with the same command and options. Name the files `<state>-before.png` and `<state>-after.png`. Remove the worktree with `git worktree remove <tmp>/base`.

**Done when** every state from step 1 has both files.

## 4. Look at every pair

Open each pair. Retake any shot that is blank, caught mid-scroll or cropped off the subject. A pair that shows no difference proves the change does not show there: drop it.

## 5. Attach

The body's wording and layout belong to the `pr` skill: the pairs go where its Evidence section shows a before and an after. Reference each file there by its local path, as a Markdown image (`![Before: …](./list-phone-before.png)`), at native resolution.

Then attach every file the body names, with the path written exactly as in the body, Markdown image being the reference form `gh` documents rewriting:

```
gh pr edit <PR> --body-file body.md --attach ./list-phone-before.png --attach ./list-phone-after.png
```

`gh pr create` takes the same flags. `gh` (2.99 or later, with write access to the repo) uploads each file and replaces its local path with the uploaded URL.

**Done when** `gh pr view <PR> --json body` shows no local `./` paths left and every image loads.
