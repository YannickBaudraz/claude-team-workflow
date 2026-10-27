# Definition of done

The standing bar every ticket clears before it counts as done. A ticket's acceptance criteria say *what* it delivers; this list says *how well*, for every ticket.

- [ ] Every acceptance criterion of the ticket is met, each with its evidence: a test, an output, or a screenshot.
- [ ] The project's full test suite passes, and so do its type check, lint and build, run with the project's own commands.
- [ ] CI is green on the PR.
- [ ] A reviewer in a fresh session reviewed the PR, and every required change is resolved or deferred to a new ticket with a reason.
- [ ] The acceptance review against the ticket returned *accepted*.
- [ ] New or changed domain terms are in the glossary; any hard-to-reverse decision is an ADR.
- [ ] Documents affected by the change are updated where the project map puts them.
- [ ] The PR description follows the PR template and links the ticket.
- [ ] The user merged it, in a terminal or in shell mode (!); the project's settings keep the agent from merging.
