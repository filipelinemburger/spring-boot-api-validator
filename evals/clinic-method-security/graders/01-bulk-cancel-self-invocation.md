---
type: llm
focus: trace
weight: 1
---

The report flags that POST /api/clinics/{clinicId}/appointments/bulk-cancel has no authorization of its own and reaches cancel() through AppointmentService.cancelAll calling it on the same object, so cancel()'s @PreAuthorize never runs (a self-call bypasses the Spring AOP proxy): any authenticated user can cancel appointments of any clinic, at its most severe level
