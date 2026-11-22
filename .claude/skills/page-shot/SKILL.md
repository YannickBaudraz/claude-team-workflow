---
name: page-shot
description: Screenshot or measure the workflow page in headless Chrome, at any width, mode, palette or grouping. Use to see a change to docs/workflow, compare a PR before and after, or check where an element sits.
---

Run `python3 docs/shoot.py` outside the sandbox (`dangerouslyDisableSandbox`); `--help` lists the options. It builds the page itself, so never write a harness page or call Chrome by hand.

- **See it:** `--shot out.png`, with `--width`, `--dark` (system) or `--theme` (pinned), `--palette`, `--group-by`, and `--at SELECTOR` to scroll there.
- **Measure it:** `--measure SELECTOR` prints each match's box in page pixels; add `--style PROPERTY` for computed values. Prefer a measurement over reading a screenshot when the question is a number.
- **See motion midway:** `--click SELECTOR` (repeatable) clicks after loading and scrolling; `--freeze MS` pauses each animation the last click starts (or, without a click, the load) that far in. Shoot a few points, e.g. 0, 100 and 300, and put them side by side.
- **Another commit:** extract it with `git archive <ref> | tar -x -C <dir>`, then pass `--root <dir>`.
- **Before and after for a PR:** follow `pr-screenshots`. Each side is `python3 docs/build-workflow.py --out <dir>/index.html`, run in a checkout at its commit, with `docs/fonts` copied beside the page, opened as a `file://` URL. On every run, leave `.version` and `.foot` out of the comparison: a commit hash and a fingerprint that differ on every build.
