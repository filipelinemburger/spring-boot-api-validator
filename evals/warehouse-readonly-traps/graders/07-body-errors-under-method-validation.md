---
type: llm
focus: trace
weight: 1
---

The report flags that on the receipts and withdrawals endpoints (where @PathVariable @Min(1) sits next to @Valid @RequestBody) an invalid body is validated through Spring 6.1 method validation and raises HandlerMethodValidationException instead of MethodArgumentNotValidException, so clients get the advice's "Invalid request parameters" error without field names rather than the field-level body errors create returns
