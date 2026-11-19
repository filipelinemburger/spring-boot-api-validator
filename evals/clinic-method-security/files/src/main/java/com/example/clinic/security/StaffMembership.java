package com.example.clinic.security;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;

@Entity
public class StaffMembership {

    public enum Role { MANAGER, RECEPTION, CLINICIAN }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String userId;

    private Long clinicId;

    @Enumerated(EnumType.STRING)
    private Role role;

    protected StaffMembership() {
    }

    public String getUserId() { return userId; }
    public Long getClinicId() { return clinicId; }
    public Role getRole() { return role; }
}
