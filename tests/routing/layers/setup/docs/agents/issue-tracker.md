# Issue tracker: local markdown

Issues live in `issues/`, one file each, named `<id>-<slug>.md`. The id is the number; `#3` is `issues/3-*.md`.

Each file starts with header lines, then the body:

- `Type:` epic, story, ticket, or issue
- `Status:` open, started, in review, or closed
- `Parent:` the parent's id, when it has one
- `Labels:` comma-separated: `bug`, `enhancement`, `ready-for-agent`, `ready-for-human`

Issues opened before 2026-10-01 have not been triaged. A document is approved when it ends with `Approved by <name> on <date>`, written when the user approves it.
