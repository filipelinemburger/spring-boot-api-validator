package com.acme.users.api;

import com.acme.users.domain.User;

public record UserResponse(Long id, String email, String displayName, String phone, boolean active) {
    public static UserResponse from(User u) {
        return new UserResponse(u.getId(), u.getEmail(), u.getDisplayName(), u.getPhone(), u.isActive());
    }
}
