---
type: llm
focus: trace
weight: 1
---

The report connects that 401 to frontend/src/api/client.ts, which clears the session and redirects to the login page on any 401, so server errors or bad requests log the user out
