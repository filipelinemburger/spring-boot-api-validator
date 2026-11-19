package com.example.clinic.appointment;

import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/clinics/{clinicId}/appointments")
public class AppointmentController {

    private final AppointmentService service;

    public AppointmentController(AppointmentService service) {
        this.service = service;
    }

    @GetMapping
    @PreAuthorize("@access.canView(#clinicId)")
    public List<AppointmentResponse> list(@PathVariable Long clinicId) {
        return service.list(clinicId);
    }

    @PostMapping
    @PreAuthorize("@access.canManage(#clinicId)")
    public ResponseEntity<AppointmentResponse> book(@PathVariable Long clinicId,
                                                    @Valid @RequestBody BookingRequest request) {
        AppointmentResponse created = service.book(clinicId, request);
        return ResponseEntity.created(URI.create("/api/clinics/" + clinicId + "/appointments/" + created.id()))
                .body(created);
    }

    @PostMapping("/{appointmentId}/cancel")
    public ResponseEntity<Void> cancel(@PathVariable Long clinicId, @PathVariable Long appointmentId) {
        service.cancel(clinicId, appointmentId);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/bulk-cancel")
    public Map<String, Integer> bulkCancel(@PathVariable Long clinicId, @Valid @RequestBody BulkCancelRequest request) {
        return Map.of("cancelled", service.cancelAll(clinicId, request.appointmentIds()));
    }

    @PostMapping("/{appointmentId}/reschedule")
    @PreAuthorize("@access.canManage(#clinicId)")
    public AppointmentResponse reschedule(@PathVariable Long clinicId, @PathVariable Long appointmentId,
                                          @Valid @RequestBody RescheduleRequest request) {
        return service.reschedule(clinicId, appointmentId, request);
    }
}
