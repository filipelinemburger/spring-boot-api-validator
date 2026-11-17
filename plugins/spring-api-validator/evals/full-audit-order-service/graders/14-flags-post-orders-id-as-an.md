---
type: llm
focus: trace
weight: 1
---

The report flags POST /orders/{id} as an update that should use PUT or PATCH, and flags PUT /orders/{id} for partial-merge semantics or for binding the Order entity as the request body
