# Coding standards

The rules a reviewer checks a diff against. They hold judgement calls only: anything a linter, formatter, type checker or test can enforce belongs in that tool, and is listed under *Enforced by tools* so reviewers skip it.

## Enforced by tools

| Rule | Tool | Command |
|---|---|---|
| Every step's needs are made by an earlier step, and every home is a row of the project map | check-contracts.py | `python3 skills/ask-team/scripts/check-contracts.py` |
| Every skill the workflow names is in the registry, installed and pinned | check-registry.py | `python3 skills/ask-team/scripts/check-registry.py` |
| The workflow page matches FLOW.md and REGISTRY.md | build-workflow.py | `python3 docs/build-workflow.py --check` |
| The merge guard refuses and allows the commands in its table | unittest | `python3 -m unittest discover -v tests/merge-guard` |
| The touches counter, the shared parser, the registry check's deny rules and the end-to-end harness | unittest | `python3 -m unittest discover tests/measures`, `tests/flow`, `tests/end-to-end` |
| Routing answers for the scenarios a change touches | tests/routing | `python3 tests/routing/run.py <scenarios> --runs 3 --model claude-opus-5-5 --effort medium` |

## Judgement calls

<Each rule: one line stating it, one line on why, and an example when the rule is not obvious. Grown by retros: a mistake a reviewer missed becomes a rule here, or a check above when a tool can catch it.>

## Reviews

- A review ends with a verdict: approve, or request changes.
- Each comment carries its weight: no prefix for a required change, `Critical:` for a merge blocker, `Nit:` or `Optional:` for the author's choice, `FYI` for information.
- Approve a change that improves the code's health, even when it isn't how the reviewer would have written it.
