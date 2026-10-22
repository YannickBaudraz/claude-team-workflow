---
name: ask-team
description: Ask which skill to run next in a project worked the way an engineering team works, from discovery to retro. A router over the team workflow's skills; with next, a short answer between two steps.
argument-hint: "[next | <request>]"
disable-model-invocation: true
model: opus
---

# Ask team

The project is worked the way a real engineering team works: discovery, roadmap, epics, refinement, tickets, test-first build, review, approval, retro. This skill tells the user which command to run next, with what arguments, in which session. It never runs the step itself: it **prints the next command**, ready to paste.

Never open, list or search `.claude/ask-team/`. The answers saved there are for the user to reread; reading them would carry an old reading into this one. The state comes only from the project map, the tracker and the documents in their homes.

Without the argument **next** alone, stop reading here: read [ROUTER.md](ROUTER.md) now, and answer in its form. The light answer below is only for **next**.

## Next: the light answer

A quick check between two steps. Read [FLOW.md](FLOW.md), and of [REGISTRY.md](REGISTRY.md) only the row of the command you print; leave ROUTER.md unread.

1. **Find what is in flight.** Find the project map (the project's `CLAUDE.md` or `AGENTS.md` points to it) and the tracker doc it names, and list the tracker's open items once.
2. **Probe the steps** of what is in flight, in order, against their outputs in FLOW.md's step contracts: is each output in its home, does a gated step's document end with its approval line (FLOW.md), are its items in the tracker. Check that each one is there; never read a document through. The first step whose output is missing or unapproved is the answer. An open sized issue outside any epic is its own line of work: its Next line is the command. So is a ticket marked ready for an agent: `/build-ticket <id>`.
3. **Answer** in this form and nothing else, its labels exactly as written, and save nothing:

   ~~~markdown
   Done up to step <n>: <what the probes found, in one line>
   **Step <n>, <name>** · <its session> · <its gate, or no gate>

   **Next**
   ```
   <the command, with the Arguments of its REGISTRY.md row, or what the user does first>
   ```
   ~~~

Hand over instead of guessing. When there is no project map, or the state takes judgement (more than one thing in flight, such as two started epics, an epic and a sized issue outside it, a wayfinder map or an issue no one has triaged; an output there without the input it needs; a choice to offer, such as a project whose roadmap is planned only when wanted with nothing in flight), say what in one line, and put `/ask-team` in the Next block.
