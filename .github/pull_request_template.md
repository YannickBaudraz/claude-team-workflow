## Ticket

<the issue this PR implements: `Closes #N`, or `Part of #N` when a later PR carries more of it>

## Before merging, read

1. The acceptance verdict: the review chain's `VERDICT:` comment on this PR.
2. The evidence and the tests below, with each change the test guards list and its reason.
3. For a UI change, the before-and-after screenshots below.
4. The full diff, only when *Merge danger* asks for it.

## Evidence

- **Before:** <failing test, output or screenshot>
- **After:** <the same, now passing>

## Tests

<The tests this PR adds or edits, one line each with its file. A test it deletes or skips goes only on its test guards line below.>

**Test guards:** <each line the test guards print, as printed, with its one-line reason in place of the placeholder; "none" when they list nothing>

## Screenshots

<For a UI change, the before-and-after pair of each screen or state it changes; otherwise "none: no UI change".>

## Merge danger

**Door:** <one-way or two-way: can this be rolled back cheaply?>

**Blast radius:** <who or what this can affect if it is wrong>

**Full diff:** <"read it" for a one-way door, a wide blast radius, or a trivial or bounded change in an existing codebase whose CI does not run its check command yet; otherwise "not needed">

## Summary

<The smallest view that makes the change clear: pseudocode, a call tree, a file tree, a component tree, a Mermaid diagram, or a diff sketch. Keep only what the reviewer needs. Use the glossary's terms.>

## Definition of done

- [ ] Acceptance criteria met, with evidence above
- [ ] Full test suite, type check, lint and build pass
- [ ] Every test the PR deletes or newly skips has its reason above
- [ ] Glossary, ADRs and affected documents updated
- [ ] Reviewed in a fresh session; required changes resolved

<!-- Shape adapted from Matt Pocock's `pr` skill (credited there to Dex Horthy, HumanLayer). -->
