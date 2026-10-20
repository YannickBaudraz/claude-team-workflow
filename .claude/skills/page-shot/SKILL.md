---
name: page-shot
description: Screenshot or measure the workflow page in headless Chrome, at any width, mode, palette or grouping. Use to see a change to docs/workflow, compare a PR before and after, or check where an element sits.
---

Run `python3 docs/shoot.py` outside the sandbox (`dangerouslyDisableSandbox`); `--help` lists the options. It builds the page itself, so never write a harness page or call Chrome by hand.

- **See it:** `--shot out.png`, with `--width`, `--dark` (system) or `--theme` (pinned), `--palette`, `--group-by`, and `--at SELECTOR` to scroll there.
- **Measure it:** `--measure SELECTOR` prints each match's box in page pixels; add `--style PROPERTY` for computed values. Prefer a measurement over reading a screenshot when the question is a number.
- **See motion midway:** `--click SELECTOR` (repeatable) clicks after loading and scrolling; `--freeze MS` pauses each animation the last click starts (or, without a click, the load) that far in. Shoot a few points, e.g. 0, 100 and 300, and put them side by side.
- **Before and after:** extract the other side with `git archive <ref> | tar -x -C <dir>`, then pass `--root <dir>`. Put the two shots side by side with `magick a.png b.png +append pair.png`.
