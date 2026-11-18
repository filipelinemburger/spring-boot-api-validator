---
type: llm
focus: trace
weight: 1
---

The report flags GET /orders/{id}/details as writing to the database (lastViewedAt set inside a @Transactional service method / dirty checking)
