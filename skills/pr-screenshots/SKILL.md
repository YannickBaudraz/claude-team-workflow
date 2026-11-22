---
name: pr-screenshots
description: "Before and after screenshots in a pull request body, attached with gh. Use when opening or updating a PR that changes what a user sees: layout, styles, copy, a rendered page or component."
---

# PR screenshots

Reviewers judge a visible change from the PR body, without checking out the branch. Give them **pairs**: one image of the base branch with what the change removes marked red, one image of the PR branch with what it adds marked green, each under a title that says what changed. Both show the same state, with the same viewport and stored settings, so the only difference is the change.

`shot-diff` makes the pairs: it opens two pages in Chrome, marks what differs and crops each image to it.

```
npx @yannickbaudraz/shot-diff@0.6.0 --help
```

Run that first. The steps below say what each run must achieve; `--help` says which option achieves it.

The tool needs an installed Chrome. Have every run stop when it finds none. Installing or downloading a browser is the user's call, whatever the tool prints: tell them and wait. When Chrome cannot start inside the Claude Code sandbox, run the command outside it.

## 1. Choose the states

List each page or state the diff changes: an open menu, an error, a grouping. A change inside closed or hidden content needs the state that opens it: a dry run lists only what its own state shows. The tool can click and set stored settings to put a page in a state.

For each, take desktop (1280 wide) and phone (390 wide), and light and dark when the project has both. Drop a combination the change cannot reach. Drop also a state or combination that would show the change exactly as a kept one does: the same words in another grouping, a change of words in dark, or at phone width when the changed part keeps its layout there.

**Done when** every visible change in the diff maps to at least one state.

## 2. Open both sides

The **before** is the base branch: the PR's base, which in a stack is the branch below it. Check it out with `git worktree add --detach <tmp>/base <base>`. A before rebuilt from memory or by undoing edits is a guess, not a pair. The **after** is the PR branch.

Build or serve each side the way the project does, taking the first that exists:

1. A project skill that runs or screenshots the app; its description says so.
2. The run command in the project map or README.
3. The `run` skill.

A built page is a `file://` URL; a served app takes one port per side.

**Done when** each side opens at its own URL.

## 3. Find the parts that changed

For each state, start with a dry run. It takes no screenshot and lists the parts of the page that changed.

A listed part the diff does not explain holds something that differs on every build: a commit hash, a timestamp. Have the tool print what it marked there, and find the element that holds it in the page's source. Leave the smallest such element out of the comparison, on this run and on every later one, and run again. Leaving out the whole listed part would hide real changes in it.

**Done when** every listed part traces to the diff.

## 4. Shoot each part

Shoot each listed part in its own run, and the whole page once when the dry run says some changes are in no part. Give each run:

- the state: every option its dry run had, what was left out of the comparison included;
- a short title that says what changed in that part: a long one wraps over several lines on a narrow image;
- its own file prefix, in one output folder for the PR, so that no run overwrites another;
- for a run of one part, the part exactly as the dry run printed it. A wider one, such as a whole section, gives an image as wide as the page;
- a device pixel ratio of 1 when the image will be narrower than the PR's text column, about 900 px, as most parts and a page at phone width are; a dry run given the part prints its width. GitHub shows such an image at its file's size, so at a ratio of 2 the part appears twice as large and twice as tall. A wider image is shrunk to the column, so it keeps the default ratio and stays sharp.

What comes back:

- A run can come back as several numbered pairs: a long part, or the whole page. Keep each pair that shows a change no other kept pair shows.
- A pair keeps both images, even when only one side has a mark.
- A run of one part reports the other parts' changes as ignored: their own runs show them. When the same run marks nothing on either image, the ignored change is the one it was meant to show: a block that exists on one side only, beside the part named. Delete its images and shoot the whole page instead.
- When a run prints any other warning, do what the warning names and run again. When it names nothing, tell the user.

**Done when** every change the dry run listed, in a part or in none, is marked on a kept image, every image narrower than the column has a file about as wide as the width its run printed, and the last run of each prints no warning but the ignored changes.

## 5. Look at every image

Open each image. Shoot again any that is blank or cropped off its subject. Once every image passes, remove the worktree with `git worktree remove <tmp>/base`.

**Done when** every image left shows its subject under its title, and the worktree is removed.

## 6. Attach

The body's wording and layout belong to `write-pr-description`: the pairs go where it puts the visual evidence for a user-visible change. Each image stands alone, referenced by its local path as a Markdown image (`![Before: …](./list-before.png)`), at native resolution.

Then attach every file the body names, with the path written exactly as in the body, Markdown image being the reference form `gh` documents rewriting:

```
gh pr edit <PR> --body-file body.md --attach ./list-before.png --attach ./list-after.png
```

`gh pr create` takes the same flags. `gh` (2.99 or later, with write access to the repo) uploads each file and replaces its local path with the uploaded URL.

**Done when** `gh pr view <PR> --json body` shows no local `./` paths left and every image loads.
