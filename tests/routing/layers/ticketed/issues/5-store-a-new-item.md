Type: ticket
Status: open
Parent: 3
Labels: enhancement, ready-for-agent

# Store a new item with its quantity

## Context
Story #3: adding a new item stores it with its quantity and unit.

## Acceptance criteria
- [ ] `pantry add rice 2kg` on an empty store stores rice at 2kg.
- [ ] `pantry add rice 1kg` after it leaves rice at 3kg.

## Verify end to end
`pantry add rice 2kg && pantry add rice 1kg && pantry list` prints `rice 3kg`.
