---
type: llm
focus: trace
weight: 1
---

The report flags that reschedule loads the appointment with findById (not scoped to the clinic), so a user who manages one clinic can reschedule another clinic's appointment by sending their own clinicId with a foreign appointment id, unlike cancel, which uses findByIdAndClinicId — at its most severe level
