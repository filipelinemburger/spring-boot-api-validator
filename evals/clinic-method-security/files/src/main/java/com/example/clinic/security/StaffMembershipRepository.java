package com.example.clinic.security;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StaffMembershipRepository extends JpaRepository<StaffMembership, Long> {

    Optional<StaffMembership> findByUserIdAndClinicId(String userId, Long clinicId);
}
