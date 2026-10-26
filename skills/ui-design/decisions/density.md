# Density, spacing and control sizing

Read this before deciding how much each region shows, whether users can change it, the spacing scale, and control, row and target sizes.

Floors: `CRAFT.md`. Body size and line height: `type.md`. Feelings: `character.md`.

## Inputs

- Input devices, the lead one, screens.
- Each region type's task (scanning or comparing many items, focused work on one, choosing an option, reading help or errors, being alerted), its frequency, and which dominates daily use.
- A predecessor, competitor or power-user habit of known density: match, exceed or depart?
- How widely density preference spreads here, from condensed layouts to large controls.
- Type, line height and icon sizes the spacing must fit; whether every component takes spacing tokens.

## Criteria and evidence

- **Task per region.** Sources agree density follows each region's task; two systems densify reading and alert regions less. The default follows the dominant region; sources disagree whether it is dense or roomy with dense opt-in. Name the harm accepted: reading and motor access, or daily efficiency.
- **Option lists.** Sources disagree: dense for efficiency, or roomier for selectable space. Weigh against the lead device's target floor.
- **Grouping.** Older evidence on plain character screens: the number and size of groups predicted search time better than fullness, so grouping is its own decision.
- **Visible size and target.** The control can shrink with density while padding or spacing holds its target at the device's floor. Floors differ by source and unit; state device and unit first. The target-size minimum of the accessibility level `CRAFT.md` targets, or its spacing exception, holds at every density; guidance recommends larger targets for frequent, hard-to-undo, edge or sequential actions.
- **Character.** Claims tying a density to a feeling are uncited, and preferred complexity at first glance varies with age and country: weak grounds; test any such claim.

## Options space

- **Two dials:** gaps between regions, padding inside components, set separately.
- **Modes:** none, user-chosen, admin or device default with user override, or set per page. Then the default; scope, app-wide or per region (sources disagree); persistence per user or device; whether text changes too (sources disagree). Do the preference spread, predecessor or devices above repay the build cost?
- **Base unit:** its anchor (root font size, body line height, icon grid, control heights) and what it must divide. Sources ground it in consistency and fewer choices; "screen sizes divide by it" is folklore.
- **Steps:** how many small ones inside components, large ones between regions; linear, geometric or mixed; tokens fixed across widths or resolved per width.
- **Control ladder:** heights per density, from line height plus padding or set directly; which siblings share a step (button beside input, table chrome with rows); row height from density and content lines; whether the target floor switches with pointer type.

## Testing

- Without users: the target-size procedure of the level `CRAFT.md` targets, on every control at each density, rows included; matching sibling heights; a grouping review; space counts against any baseline, measuring cost, not value.
- With users, per device and setting, on real content: a task measure (find or compare, errors, mis-taps) and a perception measure. Well tested: the two correlate weakly, so collect both. No controlled product test of density modes was found; speed and feel claims stay bets.

## Write down

- The lead device; each device's target floor, unit and standard.
- Each region type's density and task; default, modes, harm accepted.
- Base unit and what it divides; each step's use; the width model.
- Ladder, pairings, row heights, off-step controls and why.
- Character claims as bets; the measure that would show the density wrong.
