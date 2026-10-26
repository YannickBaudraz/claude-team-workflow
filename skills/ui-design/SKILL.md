---
name: ui-design
description: Proposes 3 reasoned UI directions for an epic, sketches them in the real app for an early look, builds and reviews the ones still in play, merges their best parts with the user, and records the epic's interface design.
argument-hint: "<epic>"
disable-model-invocation: true
---

# UI design

Step 8 of the flow, for an epic with a user interface: the interface designer's part, after the PRD and the technical design. The skill carries the design thinking: it turns the product's jobs and the user's **taste rules** into **directions**, shows them early and cheaply, then builds and reviews what is still in play. A good design usually **merges** the best parts of several directions, so the skill harvests parts across variants and the user steers the merge.

Reference files in this folder:

- `REASONING.md`: how a designer gets from jobs to directions, the direction format, and pointers to `decisions/`.
- `CRAFT.md`: the **craft floor** every screen meets in every theme the product ships, whatever the style.
- `REVIEWER.md`: the brief for the **fresh eyes** review.

The user decides; the skill shows. Every point the user has not decided (an open taste word, a recommendation taken while they were away, a finding set aside) stays visible as open, labelled as the skill's reading, until they decide it.

## 1. Load the jobs and the taste rules

- Read the project map, the epic, its PRD, its design doc for the technical limits the screens work within, and the glossary and ADRs it touches. When the epic's interface design, or the visual direction this epic writes, already exists, approved or not, review it with the user instead of starting over, then go to section 7 to fold in their changes and write the approval line.
- List the screens the epic adds or changes, and write each one's job in one line: the user's situation, what they get done there, how often. Check each job line against the epic's tasks for that screen, so no task is dropped: the review later judges only the jobs written here.
- Find the product's taste rules in its visual direction, where the project map puts it; when there is none yet, ask who the screens are for, what the product must feel like, and what they want to avoid.
- Give every rule, found or given, a **test**: how a reviewer would tell from a screenshot that a screen breaks it. Map every clause of the user's taste statement to a rule, so none is dropped.
- Ask about every rule without a test, and every assumption the user could correct, in one batched question. Ask what each vague word means to them. When examples help, offer readings that span the plausible range and say what each would look like; a single execution offered as a yes/no turns a choice into a confirmation. When an answer names something to avoid, ask what they want in its place.
- Write each rule in the user's words, with the skill's reading beside it, labelled as such. A word the user hands back or cannot pin down becomes an **open word**: recorded, and shown in step 2, never settled silently.
- Find which themes the product ships and which widths it targets, in the project map or by asking. Without an answer, use every theme the app has and the narrowest and widest widths its layout handles, and write them down as an assumption.

**Done when** every screen has its job, the themes and widths are known, and every taste rule has a test or is an open word the user knows about.

## 2. Write the directions

Read `REASONING.md`. Write the shared question and ranked criteria; every taste rule a screenshot can check counts among the criteria.

**Explore.** Start one `general-purpose` subagent with the paths of `REASONING.md` and `CRAFT.md`, the screens' jobs, the taste rules, the question and the criteria. Ask it for 8 to 10 ideas, one line each, each a different answer to the question on the structural axes, with visual language at most a mood word: typefaces, colour roles and action style are decided later, by agents that read `decisions/` first. In one list it sees its earlier ideas, so it can move each new one away from them.

**Pick.** Rank the ideas against the criteria and record the ranking in `directions.md`, one reason per idea. Pick 3 that rank well and are distinct as `REASONING.md` defines it, judged on the screen that carries the first criterion; between two that fit about equally, take the one that differs more.

**Develop.** Develop each picked idea with its own `general-purpose` subagent, all started in parallel. Give each one the paths of `REASONING.md` and `CRAFT.md`, the jobs, the taste rules with their tests, the open words, the question and criteria, and its one idea, and ask for one direction with every field of the direction format and every item each `decisions/` file asks to write down. Each direction also names the taste rule its bet strains most, with a measure, or says it strains none. Give it nothing else: the other ideas, or this conversation, would pull it towards them. Send back a direction that misses a field or a write-down item.

**Compare surfaces.** Put the three directions' surface decisions side by side: typeface roles, colour roles, how actions are treated, theme surfaces. For each choice all three share, quote the taste rule, job or existing-product constraint that forces it, or mark it open. For an open shared choice, develop one direction with it answered differently, or put it to the user below.

Save the directions in `directions.md` where the prototype will live, with the ranking, the surface table and your recommendation.

**Headline stop.** Show the user, in a few lines: the question; each direction's name, headline and the taste rule it strains, if any; the surface table, with its open choices; the top unpicked idea and why it was not picked; your recommendation. Sketch once they confirm or adjust.

**Done when** every direction has all its fields, every pair is distinct or the user knows why not, and the user has seen the headlines and the surface table.

## 3. Sketch, then build what is still in play

Use the `prototype` skill's UI branch, on the real route with the real data, one variant per direction, switchable with `?variant=`.

**Shared base.** After the directions are settled, build only what every direction agrees on (data access, formats, validation, the switcher), and settle once the conventions that are not design choices: locale, date and number formats. A builder that finds a conflict with the base reports it; reconcile reports before shooting.

**Serve.** Start the dev server so it fails rather than moving to another port, and confirm the URL serves this project before handing it on.

**Sketch.** Render first the one or two screens where each direction's bet shows, in every theme at one width, finished far enough that the look can be judged. Shoot them (step 4's rules) and show them to the user next to the headlines. This is the cheap moment to steer: drop a direction, swap a part, mix, or answer an open word.

**Build.** Build the directions still in play, scoped to the decision: the screens and states where they differ and where each bet shows, plus the states the jobs and taste rules depend on. Write down per variant what stays out for the real build. Builders look at their first screen as soon as it exists, check the facts the jobs depend on at real window heights, and work to the same self-check scope.

**Done when** every variant still in play renders on the real route in every theme the product ships, and the user has seen the sketches.

## 4. Take the screenshots

Find how the project renders, taking the first that exists: a project skill that screenshots or runs the app, the run command in the project map or README, the `run` skill. When no browser tool is installed, stop and tell the user: installing one is their call.

- **Shot list:** every screen in every theme and width, and every state the jobs and the epic name, with the clicks each state needs scripted.
- **Settings:** shoot in the target users' locale and time zone; capture window-height frames (top and scrolled) where layers are sticky or fixed; capture time-dependent states at the times `CRAFT.md` names; hide prototype-only controls.
- **Check:** open every shot and confirm it shows the state its name says, at a size where that can be seen; retake any that does not.
- Keep shots and helper scripts in a folder unique to this project and run.

**Done when** every planned shot exists and shows its state.

## 5. Review with fresh eyes

For each variant, start a `general-purpose` subagent, all in parallel. Give it the path of `REVIEWER.md`, the shots' paths with the capture settings as facts, the taste rules with their tests, each screen's job, and the points the user has dismissed. Give it nothing else: the directions and this conversation would bias it towards the work.

- **Align** findings across variants before fixing: the same problem gets the same rank and the same fix decision everywhere.
- **Fix** every blocker and major marked craft or taste, and every job major that leaves the direction itself intact. A doubtful finding gets a targeted shot before anything is built for it.
- **Verify** each fix in the state and by the measure of its finding, with the same tools as step 4. A fix that could not be verified, and every known leftover, goes to the user with the variant.
- **Only the user dismisses** a finding. A point set aside without them stays open, visible to later reviewers, and listed to the user, naming any brief line it misses.

**Done when** every variant has its review, and each blocker and major is fixed and verified, or listed to the user as open.

## 6. Merge with the user

Re-derive everything from the rendered evidence, not from the direction texts:

- **Parts worth keeping:** per variant, the parts that serve the jobs and taste rules best, from the shots and the reviews' Keep lines, each with its separable parts from the direction.
- **Strains:** per variant, every taste rule or brief line its rendered screens strain, with a measure, and every departure from an explicit brief line as "departs from: <line>".
- **Proposed merge:** the combination of parts you recommend, with the reason for each part and the conflicts between parts. Say whether this differs from your step 2 recommendation, and why. Offer one or two alternative merges.

Present the parts, strains and merges, with shots grouped so one screen and theme compares across variants, the `?variant=` URLs, every fix since the last review, what went unreviewed, and the unpicked ideas. The user adds, swaps or drops parts.

Build the merge as a variant, shoot it, and give it a fresh-eyes review of its state; tell the user this review is due before they approve. Repeat until the user approves.

**Done when** the user approves a merge or a single direction, and its final state has been reviewed.

## 7. Record the direction

Write the epic's **interface design** where the project map puts interface designs, as the direction now stands: review, merge and user changes folded into the fields and tables they change, so no later text contradicts an earlier one. It holds the shared question and criteria, the taste rules with their tests, the approved direction with every field (each part says which variant it came from), what stays out for the build, the gaps left for the build, and one line per variant and unpicked idea with why it was not taken.

Say at the top what the user did not decide: open words, the skill's readings, choices made while they were away, and whether the recorded state was reviewed after its last change. Capture the prototype as the `prototype` skill says, keeping every variant reachable, and point to its branch from the interface design.

When the product has no visual direction yet, also write its **visual direction** where the project map puts it: the taste rules with their tests, and the approved direction's surface decisions (typeface roles, colour roles, how actions are treated, theme surfaces), each with its reason. Later epics read it in section 1 and keep to it.

When the user approves, end each document with the line `Approved by <their name> on <date>`.

The build at step 11 follows the interface design. At step 12, `REVIEWER.md` reviews the built screens the same way.

**Done when** the interface design, and the visual direction when the product had none, are written with their approval lines and the prototype pointer, and the main branch holds neither the variants nor the switcher.
