---
type: llm
focus: precision
weight: 1
---

The report does not claim that GET /api/items (the list) with a currency parameter saves the converted prices: ItemService.list is @Transactional(readOnly = true), so Hibernate doesn't flush the changes. Calling the in-place pattern fragile or worth refactoring is fine; saying it writes to the database is not
