package com.example.clinic.appointment;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import java.time.LocalDateTime;

@Entity
public class Appointment {

    public enum Status { BOOKED, CANCELLED }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long clinicId;

    private String patientName;

    private LocalDateTime startsAt;

    @Enumerated(EnumType.STRING)
    private Status status = Status.BOOKED;

    protected Appointment() {
    }

    public Appointment(Long clinicId, String patientName, LocalDateTime startsAt) {
        this.clinicId = clinicId;
        this.patientName = patientName;
        this.startsAt = startsAt;
    }

    public Long getId() { return id; }
    public Long getClinicId() { return clinicId; }
    public String getPatientName() { return patientName; }
    public LocalDateTime getStartsAt() { return startsAt; }
    public Status getStatus() { return status; }

    public void cancel() { this.status = Status.CANCELLED; }
    public void moveTo(LocalDateTime startsAt) { this.startsAt = startsAt; }
}
