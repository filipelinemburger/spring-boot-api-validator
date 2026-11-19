package com.example.clinic.appointment;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import java.util.List;

public record BulkCancelRequest(@NotEmpty @Size(max = 100) List<Long> appointmentIds) {
}
