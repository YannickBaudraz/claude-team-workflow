# Form language: shape, containment, depth and state styling

Read this before deciding corner shapes, how surfaces group and layer, depth, effects behind content, and interaction states.

Floors and per-theme rendering: `CRAFT.md`. Character and loudness: `character.md`, `register.md`.

## Inputs

- Component roles: details, labels, controls, containers, page regions, floating surfaces, identity marks.
- Regions that scroll alone, float or move; backgrounds that vary.
- Density, regions per screen, layout convention, target salience.
- Character and register already set; platform limits on effects.

## Criteria and evidence

- **Roundness:** argued from audience and character, untested. Well tested on shapes and everyday objects, not interfaces: lay viewers modestly prefer curves for neutral or positive content, less with longer viewing, not for negative content; logos, typefaces, spatial designs and the few expert samples showed no reliable preference. Interface studies are small or narrow; none tests radius on real tasks, so none sets a level.
- **Containment:** sources agree on space first, raised layers last; fills, lines and shadows have no agreed order. Their reasons to go beyond space: unclear grouping, a region scrolling alone, a busy background; character and register can add one, untested. Density pulls both ways: many regions need zones told apart and leave less room for space; dense content leaves less room for containers inside it.
- **Depth:** sources give it to what floats or moves over content, a busy background, or inviting interaction beyond fill and label; character and register can add a reason, untested. Guidance gives each level a meaning; no tested guidance sets how many. One study with published methods found weak clickability cues cost search time; its authors saw less cost when density was low, layout conventional and targets salient together.
- **Effects behind content:** translucency is documented for layers over moving or varying content; sources disagree whether solid is the default elsewhere. More text needs more opacity. No tested guidance on texture or pattern was located.
- **States:** a standard and practitioners agree an outline shows focus to more users than colour alone. No study compares state methods.

## Options space

- **Radius:** by role, size, containment level, or a size-independent roundness level (sources differ); one remappable level or per component; how nested shapes and focus outlines derive.
- **Shape meaning:** sources disagree: none, or a default shape for one kind of element; shape change may carry state.
- **Separation per grouping:** space, a lifting or receding fill, a line, a shadow, a raised layer.
- **Surface levels:** how many, each with a meaning; the base; alternating or stepping from it; held at every width.
- **Depth:** which elements; levels and meanings; rendering per level (tone, shadow, line, scrim); stacking order as its own axis.
- **Effects behind content:** layer, job, opacity by text load, solid fallback for reduced transparency or raised contrast.
- **States:** one rule across components or one per family; its means (overlay, tonal step, elevation, outline, shape change); which states the product has, how their strengths order and their direction from the resting value; selected persistent and apart from pressed; focus on its own channel, and whether it follows the shape.

## Testing

- Real content on every main view and theme, every surface level and state.
- Remove each boundary: does grouping still read? Does any read as the page's end?
- Information-dense components: corners clip or crowd nothing.
- Doubtful cues: findability against flatter and stronger variants.
- States: each pair and combination told apart by users, at the smallest size; similar elements share one style.
- Effects: text over the worst backdrop, accessibility settings on.
- Roundness claims: checked with the audience; expert taste diverged from lay.

## Write down

Roundness level and reason, tested or not; radius tokens per role; derivation rules; shape meanings. Per grouping, its means and reason. Surface roles, base, nesting rule. Depth levels with meaning, members, rendering. Each effect's job and fallback. State rule, direction, selected channel, focus specification.
