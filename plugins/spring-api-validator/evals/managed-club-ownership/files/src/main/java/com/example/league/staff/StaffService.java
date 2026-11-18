package com.example.league.staff;

import com.example.league.common.ApiException;
import com.example.league.save.SaveGame;
import com.example.league.save.SaveGameService;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class StaffService {
    private final SaveGameService saves;
    private final StaffRepository staff;

    public StaffService(SaveGameService saves, StaffRepository staff) {
        this.saves = saves;
        this.staff = staff;
    }

    /** Only the managed club can hire. */
    private SaveGame requireManagedClub(UUID saveId, UUID clubId, UUID userId) {
        SaveGame save = saves.requireOwned(saveId, userId);
        if (!save.getManagedClubId().equals(clubId)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "You can only hire for the club you manage");
        }
        return save;
    }

    @Transactional
    public StaffResponse hire(UUID saveId, UUID clubId, String role, HireRequest request, UUID userId) {
        requireManagedClub(saveId, clubId, userId);
        StaffMember member = staff.findByClubIdAndRole(clubId, role).orElseGet(() -> new StaffMember(clubId, role));
        member.hire(request.name(), request.rating());
        return StaffResponse.from(staff.save(member));
    }
}
