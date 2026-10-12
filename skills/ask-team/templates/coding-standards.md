# Coding standards

The rules a reviewer checks a diff against. They hold judgement calls only: anything a linter, formatter, type checker or test can enforce belongs in that tool, and is listed under *Enforced by tools* so reviewers skip it.

## Enforced by tools

| Rule | Tool | Command |
|---|---|---|
| <formatting> | <formatter> | <command> |
| <lint rules> | <linter> | <command> |
| <types> | <type checker> | <command> |

## Judgement calls

<Each rule: one line stating it, one line on why, and an example when the rule is not obvious. Grown by retros: a mistake a reviewer missed becomes a rule here, or a check above when a tool can catch it.>

## Reviews

- A review ends with a verdict: approve, or request changes.
- Each comment carries its weight: no prefix for a required change, `Critical:` for a merge blocker, `Nit:` or `Optional:` for the author's choice, `FYI` for information.
- Approve a change that improves the code's health, even when it isn't how the reviewer would have written it.
