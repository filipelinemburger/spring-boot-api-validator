---
type: llm
focus: trace
weight: 1
---

The report flags the block() call in GET /api/products/{id}/price: on a Netty event-loop thread Reactor throws IllegalStateException, so the request fails (500); the fix is to stay reactive (flatMap)
