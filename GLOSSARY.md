# Glossary

The domain terms this repo's code uses, one entry per term. It starts empty and grows as terms come up.

**Bounded lane**: The lane for a change that is one ticket's worth of work, built through the per-ticket loop. It sits above the trivial lane, a one-sentence diff, and below the small-feature lane of two to five tickets.

**Door**: How cheaply a change can be undone, recorded with its reason in the change's risk class. A two-way door can be rolled back cheaply, while a one-way door cannot, such as a data migration, auth, payments, a public API or file format others depend on, deleting or exposing user data, or removing or moving something users rely on.

**High security class**: The deepest of the three security classes, for a project or change that touches auth, payments, exposed user data, a public API or a migration of personal data, or that holds sensitive data, money or credentials. Among other things, it adds a full threat model, a security lens on the feasibility critique and a scan before an irreversible release.

**Missed class**: A change whose risk class was set too low when it was sized, so that a check in the review chain later had to raise it. Each retro adds the narrowest path that covers such a change to CI's risky paths.

**Project facts**: The dated table in a project's map that records what differs between projects and decides which steps run: interface, deploy target, users, model-driven features, kind, exposure and data. Setup fills it, each epic retro confirms it again, and a step that depends on a fact names its fallback.

**Project kind**: The project fact, the Kind row of the map's Project facts table, that says whom a project is built for: personal, the developer's own; client, built for a client under a contract; or sold, meant to earn money. Personal is the fallback. A client project's map names the client's approver, and the client decides in writing at the approvals FLOW.md names for client projects. The Kind column of the map's document table is a different thing: a kind of document.

**Standard security class**: The middle security class, for a project that people other than its developer can reach, or that holds ordinary personal data. Below it, Baseline covers a local-only project with no personal data; Standard adds a light threat model, the PRD's security and privacy block, and abuse examples on boundary rules.
