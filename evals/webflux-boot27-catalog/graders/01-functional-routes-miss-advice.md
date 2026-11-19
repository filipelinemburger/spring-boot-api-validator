---
type: llm
focus: trace
weight: 1
---

The report flags that CategoryNotFoundException thrown from the functional /api/categories routes is not handled by the @RestControllerAdvice on this Spring Boot 2.7 / Spring Framework 5.3 WebFlux app (global advice covers WebFlux functional routes only from Spring 6.0), so a missing category reaches Boot's default error handling and returns a 500 (the exception has no @ResponseStatus) instead of the documented 404 ApiError
