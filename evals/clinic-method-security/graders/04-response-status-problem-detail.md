---
type: llm
focus: precision
weight: 1
---

The report does not claim that the ResponseStatusException(CONFLICT, "Slot already booked") bypasses ApiExceptionHandler or loses its message: the advice extends ResponseEntityExceptionHandler, which handles ErrorResponseException (and so ResponseStatusException), so clients get a 409 problem detail whose detail is "Slot already booked"
