---
type: llm
focus: trace
weight: 1
---

The report flags GET /api/products/{id}: when the product doesn't exist the Mono completes empty and WebFlux answers 200 with an empty body instead of 404
