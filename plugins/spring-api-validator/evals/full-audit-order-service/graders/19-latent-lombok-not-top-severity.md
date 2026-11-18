---
type: llm
focus: trace
weight: 1
---

The report keeps latent problems out of its most severe category: Lombok @Data recursion on the Order/OrderItem entities (nothing currently calls hashCode/equals/toString on them) is not rated Error/P0
