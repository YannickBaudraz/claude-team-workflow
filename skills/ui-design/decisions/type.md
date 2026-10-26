# Typeface and type system

Read this before deciding typefaces, type scale, weights, casing, or how type responds to width and the user.

## Inputs

- **Fixed:** scripts to render, any mandated face, the licence each surface needs, the load budget, and whether a custom face must honour native text-size and bold-text settings.
- **Real text:** content types (labels, table cells, paragraphs, identifiers, amounts, code, headline numbers), the most-used one, the smallest real size of each, longest strings.
- **Readers:** ages, vision, viewing distance, screens; each region's posture: focused task work or exploring.
- **Character and brand presence**, from `character.md` and `register.md`.

## Criteria

Sources put function before character; none ranks criteria in conflict, so this order is an inference.

1. The fixed inputs.
2. Legibility at the smallest real size each face will be set at. Well tested: reading slows once letters fall below a critical size, measured by x-height and viewing distance. Compare candidates at equal x-height or line breaks. Check look-alike glyphs, figures, features, weights and optical sizes against the real text.
3. Rendering on target platforms, and loading within the budget.
4. Character, among the faces that pass. Readers share broad associations by typeface class and judge a fitting face more appropriate: consistent in documents and advertising, untested in interfaces. Among legible faces the fastest differs per reader, preference does not predict it, and older readers lose more to a poor fit (one large study), so "it reads well to me" is weak evidence.

## Options space

- **Source:** platform fonts (no download, native settings; metrics and wraps vary by platform and locale; the look is shared with other products on the platform), one chosen face (same metrics everywhere and an identity of its own; costs loading, licence, fallback, re-implemented accessibility settings), or a mix by size or script.
- **Families:** how many, each tied to a content type; how closely x-heights and baselines match where faces share a line. Sources disagree on monospace or tabular figures for aligned numbers; reading character by character or comparing down a column can decide.
- **Scale:** a base anchored to the most-used text, set by posture and readers; steps from a rounded ratio, a generating rule or a hand-tuned list (sources disagree on method; all end on the spacing grid); as many styles as distinct roles; line height per role, perhaps two for one size.
- **Largest sizes:** how large key text gets, and whether in open regions or inside containers.
- **Weights:** each one's job (reading, text beside icons, heading, emphasis, state); headings may differ by weight alone; same-size emphasis keeps row metrics.
- **Casing:** where capitals appear. Evidence is mixed: one small study favoured capitals at equal point size; lowercase wins at matched heights and, in older work, for sustained reading.
- **Width and user:** fixed, stepped or fluid per role; which roles, if any, shrink on narrow screens, at what cost to low-vision readers. No measured benefit of fluid type was found.

## Testing

- Real content at each face's smallest real size, on the readers' screens, in every theme the product ships, against `CRAFT.md`.
- Look-alike glyphs in real identifiers; longest strings and every script, some much taller, in fixed-height components.
- Each platform, browser and locale, including the fallback during loading.
- Zoom and text-spacing override at the accessibility standard's levels; largest native text size.
- Reading-speed or character claims, tested with people of the readers' ages, or marked untested.

## Write down

Per role: size, line height, weight, family, job, where used. Then the reasons: where the base size comes from; the step method and arithmetic; how candidates were screened and compared; fallback per script; each weight's and casing's meaning; each role's response to width and zoom; which claims are tested.
