---
type: llm
focus: trace
weight: 1
---

The report flags that StockReceiptRequest uses javax.validation constraints, which Spring Boot 3 (Jakarta Bean Validation) ignores, so POST /api/items/{id}/receipts accepts a negative or missing quantity — a negative receipt lowers stock without the withdrawal endpoint's insufficient-stock check (or a missing one fails with a 500)
