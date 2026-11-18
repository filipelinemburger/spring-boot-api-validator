---
type: llm
focus: trace
weight: 1
---

The report flags that status in UpdateStatusRequest is documented as required (spec and @Schema) but not enforced, and states the real effect: a request without status fails with a 500 (a NullPointerException while building the response) instead of a 400
