---
type: llm
focus: trace
weight: 1
---

The report flags that GET /v1/orders/{orderId} documents a 404 for a missing order, but the handler's bare orElseThrow() produces a 500
