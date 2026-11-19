---
type: llm
focus: precision
weight: 1
---

The report does not claim that @Min(1) on ItemController's @PathVariable id parameters is ignored for lack of @Validated: on Spring 6.1 (Boot 3.2) built-in method validation applies it, and the advice maps HandlerMethodValidationException to 400
