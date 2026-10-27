# Craft floor

What every screen gets right in every theme, whatever its style. Each rule states what must be true, not how to achieve it, and carries its strength:

- **WCAG**: a WCAG 2.2 AA requirement; failing it is always a finding.
- **convention**: a practice most users already expect, for the reason given.
- **rule of thumb**: a practitioner rule; a starting point a direction may depart from with a reason.

A screen may depart from a convention or a rule of thumb on purpose. The departure is a finding when it visibly costs the user what the rule protects.

Every value this file leaves open (typeface, type scale, spacing scale, colours, radii, density, layout) is a design decision: the direction makes it, with its reasons.

## Contrast

- Text reaches 4.5:1 against its background; large text (24 px regular, or 18.66 px bold) reaches 3:1. Ratios are compared unrounded. Placeholders and secondary text count, on every surface they sit on, in every theme. **WCAG**
- Whatever identifies a control or its state reaches 3:1 against what is next to it: a focus ring, a selected state, a border that is the only cue that the control is there. Disabled controls and hover effects are exempt. **WCAG**
- Content the user needs to read meets the text floor whether or not they can edit it; the disabled exemption covers controls only. **WCAG**
- Thin lines render fainter than their colour: keep them above the minimum. **rule of thumb**

## Colour and themes

Every theme the product ships meets every rule on its own.

- Components use named colour roles, and each theme gives every role its own value; the direction names its roles. **convention**
- Each theme's values are chosen per role, not derived by inverting another theme. **convention**
- When the product ships several themes, they share the layout, the control metrics, the order of emphasis, and the surface levels and text tiers the direction defines, in the same number and order: a greyscale copy of each shows the same hierarchy. A colour that keeps one value across themes is checked in each. **convention**
- When the product ships more than one theme, it opens in the theme the operating system is set to, and an in-app theme choice, if there is one, defaults to following the system. **convention**
- Each text role meets its floor on the least favourable surface it sits on, in each theme. **WCAG**
- Coloured text (links, coloured labels) meets 4.5:1 on its own; when the same hue also fills components, the text gets its own value. **WCAG, convention**
- A colour made by transparency is measured on every surface it lands on: the same alpha gives a different contrast on each. **rule of thumb**
- Status carries an icon, a shape or a label besides its hue, and a colour that carries meaning keeps that meaning across the product. **WCAG, convention**
- Regions that must read as separate are separable in every theme. Where fill alone separates them, the fills differ by about ΔL\* 3.5 or more in a light theme; below that, a further cue separates them. **rule of thumb**
- A layer that floats over others (a menu, a dialog) reads as lying over what it covers in every theme, with a cue besides its shadow. In a dark theme, a floating layer no lighter than what it covers has a visible edge. **convention**
- Interaction states keep the same meaning in every theme and are visible in each. **convention**
- Status messages are legible and distinguishable from each other in every theme. Images, logos and icons stay visible against the surface they sit on in every theme, with backgrounds that belong to that theme. **convention**
- Where the direction uses colour steps, they look even in every theme; a perceptual colour space such as OKLCH helps check it. **rule of thumb**

**When the product ships a dark theme:**

- Text can pass WCAG and still read weak on dark. As an advisory second check, APCA asks for |Lc| 75 for body text, 60 for other content text and 30 for placeholders. These levels are a draft: a miss is reported as advisory, never as a failure. **rule of thumb**
- Type keeps its size and weight: light text on dark loses legibility faster than dark on light as text gets smaller. **rule of thumb, from reading studies**
- Where fill alone separates regions, the fills differ by about ΔL\* 4 or more, larger steps than a light theme needs for the same separation. **rule of thumb**

## Type

- Type sizes and weights come from one set of text styles, applied through tokens: text at the same level uses the same style everywhere, and headings take theirs from the set. The direction chooses the styles and the body size. **convention**
- Prose runs 45 to 90 characters per line. **rule of thumb**
- Numbers compared down a column line up by place value, units under units and decimals under decimals (tabular figures, which the typeface must support), with the same precision down the column, and the column's header aligns with its values. **convention**
- A command label names the specific action it performs, so the user knows what will happen before choosing it, and the same command has the same label everywhere. **rule of thumb**

## Space and hierarchy

- Every gap comes from one spacing scale, and what belongs together reads as grouped. **convention**
- What the job needs first in each region is what the eye finds first there; a region whose job is scanning similar items can keep them at one level. When a region offers actions, one at most looks like the main one. Type sizes and contrast levels meant to differ can be told apart at a glance, and emphasis is sparing enough to stand out; two levels that look almost alike are a finding. The direction states how many sizes and levels it uses, and why. **rule of thumb**
- A blurred copy and a greyscale copy of the screen both still show the intended order: the hierarchy holds without hue. **rule of thumb**

## Width

- At every width the product targets, what the job needs is whole and not squeezed past use, and no line, control or column stretches past use. The direction states what it does with extra width, and why. **convention**

## States

- Loading feedback matches the wait: none under about one second, an indicator that work is under way up to about ten seconds, and beyond that visible progress (how far along, or what is happening). When loading shows the layout's shape, it matches the real layout. **rule of thumb**
- Empty, error and partial failure are designed states: each says what happened and what to do next, and a partial failure names what succeeded and what did not. **convention**
- When something the user might expect to change is locked, the screen says why. **rule of thumb**
- Focus is visible on every interactive element, in every theme. **WCAG**

## When a screen holds a form

- Every field has a visible label, clearly tied to it. **convention**
- Errors wait until the user has finished the field. **rule of thumb**
- An error message says how to fix it in the label's words, sits on its field, and keeps what was typed. When a form has several errors, every one is findable from where the user submitted. **convention**

## When a screen holds a table

- Each row carries an identifier its users recognise, such as a name or a title, where the eye starts reading the row. When the table is sorted, the sorted column and its direction are visible. When rows can be selected, the screen shows how many are selected and what can be done with them. **convention**
