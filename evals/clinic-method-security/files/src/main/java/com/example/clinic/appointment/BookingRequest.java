package com.example.clinic.appointment;

import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record BookingRequest(
        @NotBlank @Size(max = 120) String patientName,
        @NotNull @Future LocalDateTime startsAt) {
}
