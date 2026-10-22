# Ask team: the full reading

Read the project's state, find the next step, and answer with the whole picture. [FLOW.md](FLOW.md) holds the main flow, the step contracts and the sessions; read it first.

Before naming any skill, look it up in [REGISTRY.md](REGISTRY.md): its exact command, whether Claude may load it on its own, what it calls, and the arguments that redirect it to this workflow's conventions. A skill missing from the registry is not part of the workflow.

## How to route

1. **Read the state.** Find the project map (the project's `CLAUDE.md` or `AGENTS.md` points to it). No map yet: the project is before setup. With a map, read the tracker doc it names and check what exists and what is approved: the problem statement and brief, the roadmap, each epic's design doc and PRD, its stories, tickets, open PRs, and retros, and the sized issues whose next step has not started. Read each one against the step contracts in [FLOW.md](FLOW.md): an output exists when it is in its home and its maker made it. The **frontier** is the first step whose input exists and whose output does not. When the map's Roadmap row says the roadmap is planned at step 4 only when wanted, steps 4 and 5 are not a frontier: with nothing in flight, offer `/change-request` for a change, or step 4 to plan the product.
2. **Size the request.** A change to an existing project that is not sized yet goes to `/change-request <change>` first: it diagnoses or grills the change as needed, sizes it with the user and writes it as one issue for the next session to start from; this router only reads those issues. A *spike* (one question to answer) goes to `prototype` or `research`; its answer goes on the request's issue when it has one, and the request is sized again. A *bounded* change (one ticket's worth) goes straight to the ticket path: write the ticket, then build it. An *architectural* change, or a new product, takes the main flow. Teams don't write a PRD for a typo.
3. **Answer** with: what you found for each step up to the frontier (its home and whether it is approved), the step and why it is next, which session to run it in (see Sessions in FLOW.md), what has to be approved before the step after it, the next command with its arguments, and what comes after it. Always in this form, so the user finds each part in the same place:

   ~~~markdown
   | Step | Home | Found | Approved |
   |---|---|---|---|
   | <each step up to the frontier> | <its home> | <what is there, or **missing**> | <yes and the date, **no**, or no gate> |

   **Step <n>, <name>.** <why it is next: its input exists and its output does not>
   **Session:** <which session runs it>
   **Gate:** <what the user approves before the step after it, or none>

   **Next**
   ```
   <the command with its arguments>
   ```

   **After that:** <the steps that follow, in order, each with its command, its gate, and what it leaves when done (its outputs in the step contracts): at least the next one, and on through this session's steps>
   ~~~

   The table is how the user catches a misread state before running anything: name what you did not find as plainly as what you did. When a gate or a choice comes before any command can run, the Next block says what the user does first, and never holds a command that cannot run yet; for a choice, one line per option. Done when the user can paste the Next block and knows where.
4. **Save the answer** when it is about the project in this folder: the one whose map you read, or the codebase you are setting up; never for an idea asked from another project's folder. Save it, exactly as printed, in `.claude/ask-team/` of the main checkout (the first path `git worktree list` prints; this folder when it is not a git repo), without opening anything already there: write it as a new file, `<yyyy-mm-dd-hhmm>-<step-n or the way in>.md`, starting with the date and the commit, then in one shell command copy it over `latest.md` and write `*` into `.claude/ask-team/.gitignore`, so git ignores the folder whatever the project's own rules say. These files are all this skill writes. When nothing was saved, say why in one line.

## Ways in

- A feature, an improvement or a bug fix the user brings to an existing project: `/change-request <change>`.
- A bug report or request that arrived from outside: `/triage`. A bounded one it marks ready for an agent is already a ticket, built at step 10; anything bigger is marked ready for a human, and `/change-request <issue>` then sizes it from its brief, without a second grilling.
- Something broken that resists a first look: `diagnosing-bugs` loads on its own; for a hard one, `/diagnosing-bugs` explicitly.
- Production incident: `/engineering:incident-response`.
- A huge, foggy effort: `/change-request <effort>`, like any change. When the way is unclear, its Next line sends the effort to `/wayfinder`; once the map clears, `/change-request <map>` sizes and places it, instead of going straight to step 4.

## Any time

`research` (a cited write-up of primary sources), `codebase-design` (deep-module vocabulary), `domain-modeling` (a contested term, an ADR), `wizard` (steps only the user can take), `lesson-learned`, `/handoff` (only when the work moves to another folder, tool or person).

## Maintenance

After installing, removing or updating a skill of this workflow, or changing SKILL.md, ROUTER.md or FLOW.md, update [REGISTRY.md](REGISTRY.md), its Does line included, and run `python3 ~/.claude/skills/ask-team/scripts/check-registry.py`. It checks that every skill these files name is in the registry, that each skill's visibility matches the settings, that no skill calls one Claude cannot load, that the step contracts close, through `scripts/check-contracts.py`, and that the workflow page can still be built from these files and the registry. CI runs the contract check on every pull request. The contract check proves that no hand-off is missing, not that a skill does what its row says; `tests/routing/run.py` in this repo runs this router on fixture projects and checks the command it answers. Run it after changing them, in both modes. When a real project gets a wrong answer, add its state as a scenario there before fixing the router. GitHub publishes that page on every push to `main`.
