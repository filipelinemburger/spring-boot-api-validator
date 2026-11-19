---
type: llm
focus: trace
weight: 1
---

The report flags that the class-level @Validated on ReportController makes out-of-range threshold/limit values throw ConstraintViolationException, which ApiExceptionHandler doesn't handle, so clients get a 500 instead of a 400 — and the fix is to remove the class-level @Validated (Spring 6.1's built-in validation then raises HandlerMethodValidationException, already mapped to 400) or to handle ConstraintViolationException
