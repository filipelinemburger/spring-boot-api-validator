package com.example.clinic.appointment;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AppointmentRepository extends JpaRepository<Appointment, Long> {

    Optional<Appointment> findByIdAndClinicId(Long id, Long clinicId);

    List<Appointment> findAllByClinicIdOrderByStartsAt(Long clinicId);

    boolean existsByClinicIdAndStartsAtAndStatus(Long clinicId, LocalDateTime startsAt, Appointment.Status status);
}
