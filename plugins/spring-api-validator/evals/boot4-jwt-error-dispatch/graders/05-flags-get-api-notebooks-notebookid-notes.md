---
type: llm
focus: trace
weight: 1
---

The report flags GET /api/notebooks/{notebookId}/notes/{noteId} for a missing note calling orElseThrow() without an exception (NoSuchElementException instead of 404 NOTE_NOT_FOUND, unlike delete)
