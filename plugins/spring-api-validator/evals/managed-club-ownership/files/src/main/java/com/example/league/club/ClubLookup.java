package com.example.league.club;

import com.example.league.common.ApiException;
import org.springframework.stereotype.Component;

import java.util.UUID;

@Component
public class ClubLookup {
    private final ClubRepository clubs;

    public ClubLookup(ClubRepository clubs) { this.clubs = clubs; }

    /** The club must exist in this save. */
    public Club requireInSave(UUID saveId, UUID clubId) {
        return clubs.findById(clubId)
                .filter(c -> c.getSaveId().equals(saveId))
                .orElseThrow(() -> ApiException.notFound("Club"));
    }
}
