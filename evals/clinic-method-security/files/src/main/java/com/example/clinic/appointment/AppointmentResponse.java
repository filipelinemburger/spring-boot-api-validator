package com.example.clinic.appointment;

import java.time.LocalDateTime;

public record AppointmentResponse(Long id, Long clinicId, String patientName, LocalDateTime startsAt, String status) {

    static AppointmentResponse from(Appointment a) {
        return new AppointmentResponse(a.getId(), a.getClinicId(), a.getPatientName(), a.getStartsAt(), a.getStatus().name());
    }
}
