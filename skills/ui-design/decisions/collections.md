# Collection views

Read this before deciding how a screen lays out, filters and loads many records.

Record tasks: `REASONING.md`. Floors: `CRAFT.md`. Row height: `density.md`. Narrow widths: `layout.md`. Item pages and where they open: separate decisions.

## Inputs

- Dominant task per role: overview, browse, find a known item, narrow, compare, triage, reorder, act in bulk.
- Item count, load time, records changing mid-browse.
- Shared or varied attributes; identity by text or by image.
- Relations: flat, grouped by a value, or parent and child.
- Filter profile: properties, value types, logic needed, space.

## Criteria and evidence

- **View.** Guidance agrees aligned columns serve comparing shared attributes. Sources disagree on cards for comparison: against, as cards vary in structure; for, when items are recognised by their look. Name which comparison: one attribute across many items, or a few judged whole. Item-count thresholds differ by source, unevidenced. A view keyed to one attribute needs that field and a task it serves.
- **Switching.** Guidance agrees: every view renders the data, the default serves the main task, the choice persists; benefit untested.
- **Columns.** Sources disagree on order: by task importance, long text last; or matching the create form. Name the principle and the tiebreak. Default sort: the question the top row answers, or the data's own order; convention. Guidance scales column control with column count and comparison work, reachable without dragging, state visible.
- **Aids.** Each answers: could users lose their column or row? Striping is the most tested aid, modestly and on small tables: no measured harm, sometimes more accurate under time pressure, preferred by a plurality. Fixed headers and columns are untested. How well an aid is tested says how sure a choice is, not whether this table needs it.
- **Filters.** Richer models cost more to build and use: name each gain. Sources disagree on the default, instant or applied; they agree an apply step suits many criteria and slow queries, instant updates exploration (consumer-site evidence).
- **Persistence.** Restore on return, named views for recurring setups, a shareable link: each its own trigger. System rationale only.
- **Long lists.** Weak, mixed evidence: no method won one controlled study. Systems disagree: pages, for position, size and selection scope, or loading on scroll or request. Guidance ties pages to finding, comparing distant items and inspecting the top, continuous loading to browsing.
- **Hierarchy.** A group is a view (derived counts, no editing) or a real object (selectable, editable). Guidance moves levels with different fields, or deep ones, out of the table; convention only.

## Options space

- **View:** table, list, cards, grid, feed, keyed to one attribute; one or several, switched by user or width.
- **Columns:** identifier, and whether it opens the record; visible, hidden, fixed sets; control from none to hide, reorder, resize, freeze.
- **Aids:** fixed header or identifier, overflow cue, striping, borders, row hover; default or preference.
- **Filters:** search, simple filters, facets, attribute tokens, rule builder; instant or applied; starting values; how active filters, hidden ones too, show and clear.
- **Persistence:** restored, named, shipped, shared; who edits shared views; how unsaved changes show.
- **Loading:** numbered pages, previous and next, load more, continuous; page size.
- **Per level:** counters, aggregates, what filters keep, sort, paging, selection reach.

## Testing

- Sessions on the dominant task: find a named record, compare distant records, act on a filtered set, return after opening one. Measure accuracy, time, browsing depth, lost place; split-test each assumption alone.

## Write down

- Task, record and filter profiles, each choice traced to them; thresholds as conventions; the side taken where sources disagree.
- Selection and scroll after an update; what zero results offers; what stays out of a link.
