package com.example.clinic.appointment;

import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record RescheduleRequest(@NotNull @Future LocalDateTime startsAt) {
}
