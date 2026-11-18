---
type: llm
focus: trace
weight: 1
---

The report flags PUT /api/books/{id}/stock taking @RequestBody UpdateStockRequest without @Valid, so @field:Min(0) never runs (negative stock is stored)
