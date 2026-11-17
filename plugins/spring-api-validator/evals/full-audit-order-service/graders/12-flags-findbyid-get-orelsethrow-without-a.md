---
type: llm
focus: trace
weight: 1
---

The report flags findById(...).get() / orElseThrow() without a mapped exception as producing 500 instead of 404 for missing orders
