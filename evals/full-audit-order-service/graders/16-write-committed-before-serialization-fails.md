---
type: llm
focus: trace
weight: 1
---

The report points out that write endpoints returning the entity commit the change before serialization fails, so the client sees a 500 for a saved write (risking duplicate retries)
