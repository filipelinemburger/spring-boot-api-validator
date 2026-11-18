---
type: llm
focus: trace
weight: 1
---

The report does not claim that NotFoundException thrown from the functional StockHandler bypasses the @RestControllerAdvice: on Spring Framework 6 (Boot 3.3) global advice also handles errors from functional routes, so it becomes a 404 ApiError
