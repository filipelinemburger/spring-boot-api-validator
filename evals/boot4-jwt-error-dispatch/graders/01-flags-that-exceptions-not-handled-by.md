---
type: llm
focus: trace
weight: 1
---

The report flags that exceptions not handled by GlobalExceptionHandler are forwarded to /error, which requires authentication, so the client receives 401 instead of the real error (because the JWT authentication set by JwtAuthFilter is not available on the error dispatch)
