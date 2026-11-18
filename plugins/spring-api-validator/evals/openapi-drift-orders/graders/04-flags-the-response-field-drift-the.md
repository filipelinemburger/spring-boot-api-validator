---
type: llm
focus: trace
weight: 1
---

The report flags the response field drift: the spec's OrderResponse has orderNumber, but the DTO serializes number, so clients never receive orderNumber
