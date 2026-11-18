---
type: llm
focus: trace
weight: 1
---

The report notes that because the isbn @Size is ignored, an ISBN longer than 13 characters reaches the VARCHAR(13) column and fails as a database error instead of a 400
