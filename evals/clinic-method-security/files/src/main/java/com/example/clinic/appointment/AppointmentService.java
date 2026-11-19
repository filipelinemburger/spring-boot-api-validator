package com.example.clinic.appointment;

import com.example.clinic.common.NotFoundException;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
@Transactional
public class AppointmentService {

    private final AppointmentRepository appointments;

    public AppointmentService(AppointmentRepository appointments) {
        this.appointments = appointments;
    }

    @Transactional(readOnly = true)
    public List<AppointmentResponse> list(Long clinicId) {
        return appointments.findAllByClinicIdOrderByStartsAt(clinicId).stream().map(AppointmentResponse::from).toList();
    }

    public AppointmentResponse book(Long clinicId, BookingRequest request) {
        requireFreeSlot(clinicId, request.startsAt());
        Appointment saved = appointments.save(new Appointment(clinicId, request.patientName(), request.startsAt()));
        return AppointmentResponse.from(saved);
    }

    @PreAuthorize("@access.canManage(#clinicId)")
    public void cancel(Long clinicId, Long appointmentId) {
        Appointment appointment = appointments.findByIdAndClinicId(appointmentId, clinicId)
                .orElseThrow(() -> new NotFoundException("Appointment " + appointmentId + " not found"));
        appointment.cancel();
    }

    /** Front desk closes for the day: cancel a batch of appointments. */
    public int cancelAll(Long clinicId, List<Long> appointmentIds) {
        appointmentIds.forEach(id -> cancel(clinicId, id));
        return appointmentIds.size();
    }

    public AppointmentResponse reschedule(Long clinicId, Long appointmentId, RescheduleRequest request) {
        Appointment appointment = appointments.findById(appointmentId)
                .orElseThrow(() -> new NotFoundException("Appointment " + appointmentId + " not found"));
        requireFreeSlot(clinicId, request.startsAt());
        appointment.moveTo(request.startsAt());
        return AppointmentResponse.from(appointment);
    }

    private void requireFreeSlot(Long clinicId, LocalDateTime startsAt) {
        if (appointments.existsByClinicIdAndStartsAtAndStatus(clinicId, startsAt, Appointment.Status.BOOKED)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Slot already booked");
        }
    }
}
