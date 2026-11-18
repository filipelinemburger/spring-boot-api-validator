package com.example.league.tactics;

import java.util.UUID;

public record TacticsResponse(UUID clubId, String formation, String mentality, UUID captainId) {
    static TacticsResponse from(Tactics t) {
        return new TacticsResponse(t.getClubId(), t.getFormation(), t.getMentality(), t.getCaptainId());
    }
}
