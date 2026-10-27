# Record pages, attributes and value display

Read this before structuring a record's page and deciding how its values, labels and user-content previews display.

Floors: `CRAFT.md`. Colour sets: `colour.md`. Where details open, editing and collection views are separate decisions.

## Inputs

- Whether the job needs a record page, or a list, guided flow, find-by-identifier entry or analysis view.
- Tasks on the record and which reach related records; groups read together or compared; volume per group.
- Identity: name, identifier or both; whether importance varies by role.
- Per value: the reader's next step (judge recency, act at a moment, audit, reconcile, compare); the data's accuracy; domain constraints (billing unit, time zone, legal record).
- Per label: does it change the next action, describe, count, or mark a technical state? Who defines its meaning and how it shows?
- Per preview: scanning many or inspecting one; whether content identifies itself visually.

## Criteria and evidence

- **Structure:** sources tie one page to one task or groups read together, tabs to independent, large, uncompared groups, a hub to tasks reaching related records. Practitioner guidance, without data: hidden content gets missed; cross-tab comparison taxes memory. Count thresholds are convention; no controlled study compares structures.
- **Header:** sources admit by scope: identity, values every task needs, actions and messages on the whole record. No published method picks key attributes; two sources make them configurable.
- **Time:** sources disagree on the default, relative or absolute; neither cites evidence. One gives absolute to audit, legal and security records, ranges, and anything users would convert. Both reach full absolute time from a shortened form.
- **Precision:** guidance for few significant digits rests on other guidelines, not reader tests: weak evidence. Research, known from a summary, finds more digits read as more confidence: digits are a claim; too few hide needed differences.
- **Absence:** sources agree zero is not absence; they disagree between one mark for all and words by meaning. Either way, screen readers skip empty cells and misread punctuation: each mark needs a name they announce.
- **Labels:** sources agree, untested: role sets prominence and treatment (colour set, component, or plain text). Count limits lack evidence.
- **Previews:** one study, abstract only: cropping to the important region aids small-size recognition. Later research found an automatic cropper skewed across demographic groups on images of people, and recommended user control.

## Options space

- **Structure:** one page, anchored sections, tabs, a hub of related collections; what stays visible.
- **Header:** membership, configurability, scroll and narrow behaviour.
- **Time:** relative, absolute or both, per value; granularity; event label and actor; time zone.
- **Numbers:** digits, unit, scale, how direction of change shows.
- **Absence:** a vocabulary first (not set, not applicable, none by intent, unknown, failed to load, zero), then marks.
- **Several labels:** show all, roll up to the most severe, overflow, plain text. A roll-up needs a route to its cause; no source covers one.
- **Previews:** crop, original ratio, or type mark with metadata; who picks the crop; a placeholder by item kind, doubling as fallback or not.

## Testing

- Usage of each structural control and field; key content fitting the target width: one vendor's method, weak evidence.
- Real volumes and edge values: longest name, zero, empty, many labels, failed previews.
- A screen reader on absence marks and truncated labels; crops on images of people; task timing against a baseline.

## Write down

Record page or another form, and why; structure and what rules out the others; header set and its test; each value type's format and reason, and any route to the other form; precision; absence vocabulary and marks; label classes with owner, prominence, summary; preview mode per view, crop owner, fallback; sides taken.
