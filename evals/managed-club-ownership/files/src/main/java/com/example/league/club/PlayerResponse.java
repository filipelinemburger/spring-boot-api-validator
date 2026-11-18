package com.example.league.club;

import java.util.UUID;

public record PlayerResponse(UUID id, String name, String position, int overall) {
    public static PlayerResponse from(Player p) {
        return new PlayerResponse(p.getId(), p.getName(), p.getPosition(), p.getOverall());
    }
}
