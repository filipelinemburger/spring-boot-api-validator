---
type: llm
focus: trace
weight: 1
---

The report flags that the LocalDate from/to parameters of GET /api/products/released have no @DateTimeFormat (and no spring.webflux.format.date), so on Spring 5.3 ISO dates such as 2026-01-01 — the format the endpoint documents — fail to convert and the request gets a 400
