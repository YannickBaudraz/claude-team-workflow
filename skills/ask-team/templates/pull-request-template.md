## Ticket

<link to the ticket this PR implements>

## Before merging, read

1. The acceptance verdict: the review chain's `VERDICT:` comment on this PR.
2. The evidence and the tests below, with each change the test guards list and its reason.
3. For a UI change, the before-and-after screenshots below.
4. The full diff, only when *Merge danger* asks for it.

## Evidence

- **Before:** <failing test, output or screenshot>
- **After:** <the same, now passing>

## Tests

<The tests this PR adds, edits or deletes, one line each with its file.>

**Test guards:** <each line the test guards print, with its one-line reason in place of the placeholder; "none" when they list nothing>

## Screenshots

<For a UI change, the before-and-after pair of each screen or state it changes; otherwise "none: no UI change".>

## Merge danger

**Door:** <one-way or two-way: can this be rolled back cheaply?>

**Blast radius:** <who or what this can affect if it is wrong>

**Full diff:** <"read it" for a one-way door, a wide blast radius, or a change built while CI does not run the test guards; otherwise "not needed">

## Summary

<The smallest view that makes the change clear: pseudocode, a call tree, a file tree, a component tree, a Mermaid diagram, or a diff sketch. Keep only what the reviewer needs. Use the glossary's terms.>

## Definition of done

- [ ] Acceptance criteria met, with evidence above
- [ ] Full test suite, type check, lint and build pass
- [ ] Every test the PR deletes or newly skips has its reason above
- [ ] Glossary, ADRs and affected documents updated
- [ ] Reviewed in a fresh session; required changes resolved

<!-- Shape adapted from Matt Pocock's `pr` skill (credited there to Dex Horthy, HumanLayer). -->
