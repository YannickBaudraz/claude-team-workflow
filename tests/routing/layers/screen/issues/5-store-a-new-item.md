Type: ticket
Status: open
Parent: 3
Labels: enhancement, ready-for-agent

# Add an item from the pantry's page

## Context
Story #3: a cook adds an item from the page. The page is the epic's first screen. It runs on the standard library's `http.server`, and items stay in the store `src/pantry.py` already reads.

## Acceptance criteria
- [ ] `python3 src/pantry.py serve <port>` serves the page at `/`, listing each item with its quantity.
- [ ] With nothing stored, the page says `Nothing in the pantry yet.`
- [ ] The page's form posts `name` and `quantity` to `/items`; afterwards the page lists the item.
- [ ] Posting rice `2kg`, then rice `1kg`, lists rice at `3kg`.
- [ ] Posting rice `500g` after that keeps rice at `3kg`, and the page says `Use the same unit as before.`
- [ ] Posting an empty name stores nothing, and the page says `Give the item a name.`

## Verify end to end
Serve the page, add rice `2kg` and rice `1kg` through its form, and read rice at `3kg` on the page.
