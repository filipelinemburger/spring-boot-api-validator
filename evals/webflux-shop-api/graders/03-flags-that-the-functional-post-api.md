---
type: llm
focus: trace
weight: 1
---

The report flags that the functional POST /api/stock/{sku}/reservations handler reads ReservationRequest with bodyToMono and never validates it, so @NotBlank/@Positive don't apply
