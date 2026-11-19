package com.example.clinic.security;

import java.util.EnumSet;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

/** Used from @PreAuthorize expressions: @access.canView(#clinicId), @access.canManage(#clinicId). */
@Component("access")
public class ClinicAccess {

    private final StaffMembershipRepository memberships;

    public ClinicAccess(StaffMembershipRepository memberships) {
        this.memberships = memberships;
    }

    public boolean canView(Long clinicId) {
        return memberships.findByUserIdAndClinicId(currentUserId(), clinicId).isPresent();
    }

    public boolean canManage(Long clinicId) {
        return memberships.findByUserIdAndClinicId(currentUserId(), clinicId)
                .filter(m -> EnumSet.of(StaffMembership.Role.MANAGER, StaffMembership.Role.RECEPTION).contains(m.getRole()))
                .isPresent();
    }

    private String currentUserId() {
        return SecurityContextHolder.getContext().getAuthentication().getName();
    }
}
