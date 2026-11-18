package com.example.league.staff;

import java.util.UUID;

public record StaffResponse(UUID id, String role, String name, int rating) {
    static StaffResponse from(StaffMember m) {
        return new StaffResponse(m.getId(), m.getRole(), m.getName(), m.getRating());
    }
}
