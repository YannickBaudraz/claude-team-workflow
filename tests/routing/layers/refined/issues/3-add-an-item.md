Type: story
Status: open
Parent: 1
Labels: enhancement

# Add an item

As a cook, I add an item with a quantity, so the pantry knows I have it.

## Rules
- Adding an item that exists adds to its quantity; the units must match.

## Examples
- `pantry add rice 2kg` then `pantry add rice 1kg` leaves rice at 3kg.

## Acceptance criteria
- [ ] Adding a new item stores it with its quantity and unit.
- [ ] Adding to an existing item in another unit is refused with a message.
