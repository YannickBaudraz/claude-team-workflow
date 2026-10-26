# How a designer reasons

How to get from a product's jobs to a direction worth rendering.

## Decide from the job down

Every decision sits on a plane, and each plane is settled before the one below it:

1. **Job:** the situation the user is in and what they are trying to get done. Settled by the grilling; restate it in one line per screen.
2. **Scope:** which jobs this screen serves and which it hands to another screen.
3. **Structure:** where the screen sits in the product, and what the user works with there.
4. **Hierarchy:** what the screen makes obvious first and what comes second, ranked from the job. Ask what the user came to find out, which action, if any, means the screen worked, and what they need to see before taking it; rank from the answers and write the ranking down.
5. **Skeleton:** layout, and where the elements the job depends on sit. Before deciding the grid, width and scrolling, read `decisions/layout.md`; before deciding the shell and navigation, `decisions/navigation.md`.
6. **Surface:** colour, type, form, motion, tone. Each of these is a decision with its own reasoning: before deciding one, read its file in `decisions/` (`character.md` for what the product should feel like, `register.md` for how expressive it is and how much brand it shows, `colour.md`, `type.md`, `density.md` for density and spacing, `form.md` for shape, containment and depth, `icons.md` for icons and identity marks).

Sketch the core content before what surrounds it: it tells you what the structure has to hold. Every element has a reason you can name: a job it does, a taste rule it serves, or what the direction's visual language says to these users.

When the grilling left open something a decision depends on, write it as a named assumption.

## Use over time

For each screen, write how often and for how long the user is on it, and what they already know when they arrive. From that, the job and the taste rules, decide how much the screen shows at once, how it keeps navigation within reach and how much it explains, and give the reason. The screen works for users who never learn its shortcuts.

When the jobs carry worries for the user, list them first and note where on the screen, or in its flow, the user finds the answer to each one.

## When a screen holds many records, a data summary or a form

Before deciding how a set of records is shown, read `decisions/collections.md`; before deciding a single record's page, `decisions/records.md`; before placing actions and choosing how editing works, `decisions/actions.md`.


- Many records, whatever form they take, serve four tasks: finding records, comparing them, viewing or editing one, and acting on several. Name the one that dominates on this screen, from the job: it shapes the structure. When the job leaves it open, say so, and each direction's bet names the one it assumes. When users judge a record against its neighbours, editing it keeps them in view.
- Before placing anything on a screen that summarises data, decide from the job what the user does with it next, such as act now, investigate, report onward or confirm that all is well.
- When the user compares quantities, show them by position or length, which people compare most accurately; magnitude needs more than colour or area alone.
- A form's goal is completion: judge each choice by whether more people finish it correctly, and keep what they typed when something fails.

## Familiar and new

When the product already has screens, components or a brand, read `decisions/existing-product.md` before writing any direction: it decides how far the new screens follow what exists.


Decide, from the jobs and the taste rules, where the screen follows what its users already know and where it departs. Every choice, familiar or new, names the job, user moment or taste rule it serves. A departure also names what it costs to learn, who pays that cost, and how often they use the screen; a familiar choice names what it gives up for this job and these users.

## Writing a direction

A direction is one answer to a question shared by all directions. Write the reasons first, then the screen: reasons written afterwards rationalise whatever came out.

**Shared, written once by the skill:**

- **Question:** the screen's core problem as a user problem: how does this user get this job done in this situation?
- **Criteria:** the user needs and product goals every direction is judged against, ranked.

**Per direction:**

| Field | Content |
|---|---|
| Name and headline | One or two "X, even over Y" statements for this screen, where Y is something a reasonable team could choose instead. |
| Design model | Its answer on each design axis below. |
| Wins and loses | Which criteria it serves and which it sacrifices. |
| The bet | The assumption about users that must hold for it to win. |
| Choose it when | The condition under which it is the right answer. |
| Limits | What it deliberately leaves out, and where it is risky. |
| Tone | Each tone word tied to concrete parameters within the taste rules, and to the user moment it serves. |
| Separable parts | Which decisions could move into another direction, and which depend on each other. |

## Design axes

Each axis is a question every direction answers from the jobs:

- **Starting point:** what does the user land on, and what do they work with?
- **Task model:** in what order does the user get the job done?
- **Whole and parts:** when the job has a whole and its parts, how does the user move between them, and what stays in view?
- **Density and disclosure:** how much is shown at once, and what is revealed when?
- **Actions:** which actions does the job need, and where does each live?
- **Navigation:** how does the user move between the screen's parts and the rest of the product?
- **Visual language:** what do colour, type, form and motion say about the product to these users, and why? 'None' is a valid answer for motion, with its reason.

Add an axis when the jobs or the taste rules make another decision decisive.

Directions are **distinct** when a user shown them side by side would describe them as different answers to the question, and at least one of their differences is structural, on the screen that carries the first criterion. The **grayscale test** checks it: picture each direction as a grayscale wireframe, and distinct structures give different wireframes. Two directions that share one structure are one direction in two visual languages. A structure counts as reasonable only when it serves the ranked criteria. When the jobs leave only one reasonable answer on an axis, say so, and let the directions differ where they can; when they leave only one reasonable structure, that is an expected outcome, not a shortfall: tell the user, and the directions then differ in visual language within the taste rules.
