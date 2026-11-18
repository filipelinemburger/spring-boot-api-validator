package com.example.league.staff;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface StaffRepository extends JpaRepository<StaffMember, UUID> {
    Optional<StaffMember> findByClubIdAndRole(UUID clubId, String role);
}
