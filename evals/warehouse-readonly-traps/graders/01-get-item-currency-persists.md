---
type: llm
focus: trace
weight: 1
---

The report flags that GET /api/items/{id} with a currency parameter converts the item's price and currency in place inside ItemService.get, a read-write @Transactional method, so the converted values are flushed to the database (a read permanently changes the stored price, compounding on repeated calls), at its most severe level
