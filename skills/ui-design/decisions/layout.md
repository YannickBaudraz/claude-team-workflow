# Layout grid, width, scrolling and adaptation

Read this before deciding which window sizes to support, how screens use width, what changes between sizes, and what scrolls or stays fixed.

Floors: `CRAFT.md`. Shell regions and evidence on hiding navigation: `navigation.md`.

## Inputs

- The product's own evidence: window sizes, places of use, which tasks happen where, how often. Sources agree: decide by window, which resizing and zoom change, not device.
- The floor: the accessibility level `CRAFT.md` targets requires reflow at a narrow zoomed width, even with no phone targeted.
- Input: touch, pointer, keyboard, mixed at any width; what relies on hover.
- Content class per screen: reading, form, structured overview, many like items, horizontally unbounded, one item in context.

## Criteria

- **Scope per size.** Sources disagree: the same functionality everywhere, less of it visible, since nobody knows what a narrow-window user wants; or a streamlined set where evidence shows where work happens. The first fits one product seen narrow, the second a companion app. Name the side and evidence.
- **Lead size.** A process choice without outcome evidence: starting small forces priorities, starting large makes the full version usable first. Where do frequent, critical tasks happen? Check the other end early.
- **Extra width.** Does the user want more things, or more of each? Dense content lowers the pane count at mid widths. One small study favours side by side for multi-part work; weak transfer to panes.
- **Fixed elements.** Is it used repeatedly while scrolling what it serves, and what height does it cost when narrow or zoomed? Sources disagree on fixing the global header; this test decides.

## Options space

- **Ambition per size:** works, optimised, or designed for.
- **Width model per content class:** capped or not, where a cap sits, what extra width buys (more items, bigger items, more panes, revealed controls, margin). Sources disagree on capping overview screens; ask the more-things question.
- **Grid:** a column grid, or regions sized by their content; for columns, the count from the component base or the content; fixed boxes or fluid columns; gutters by how separate pieces are; what aligns and what follows the spacing scale. Alignment serves coherence; evidence it speeds use is weak and mixed.
- **Breakpoints:** found by widening real content until it breaks, from the component base, or both. Values are conventions, differing widely; let the content set how many change structure and how many only adjust.
- **What responds:** the viewport, or each region's own space.
- **Moves per region:** reveal, divide, resize, reposition, swap for a functionally equivalent component, hide, re-architect. Narrow form follows role: navigating, acting on the view, or supporting it.
- **Narrow tables:** visible overflow, locked identifier column, filter first, chosen columns, one item per card, all untested; by comparing rows or looking up one.
- **Scrolling:** static, fixed, toggleable or partly persistent, per element and size; panes scrolling alone to keep a selection in view; nesting axes; scroll chaining at an area's end.

## Testing

- Shots at the narrowest required width, either side of each structural breakpoint, the widest target, the standard's zoom on a desktop window, a larger browser font.
- Live: resizing, opening panels; keyboard reach of scroll areas; focus at least partly visible past fixed content (standard).
- Every region's actions reachable at each size; an editing toolbar in view with its content.
- Discoverability, page length and reduced scope with representative users; analytics re-checked regularly.

## Write down

Per screen class: content class, width model, breakpoints with each region's move and narrow form, what responds to what, fixed elements and why, scope and ambition per size with evidence, lead size, sides taken in disagreements.
