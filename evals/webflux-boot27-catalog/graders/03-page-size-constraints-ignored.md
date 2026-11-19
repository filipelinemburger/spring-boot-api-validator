---
type: llm
focus: trace
weight: 1
---

The report flags that @Min/@Max on GET /api/products' page and size request parameters are not applied, because before Spring 6.1 constraints on method parameters need class-level @Validated, and states a concrete consequence (for example a negative size making skip/take throw IllegalArgumentException and a 500, or an unbounded page size)
