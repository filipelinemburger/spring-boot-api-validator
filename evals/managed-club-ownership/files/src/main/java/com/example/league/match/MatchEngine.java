package com.example.league.match;

import com.example.league.tactics.Tactics;
import com.example.league.tactics.TacticsRepository;
import org.springframework.stereotype.Component;

import java.util.UUID;

/** Simulates a fixture. Both sides play with their stored tactics; clubs without any use the AI default. */
@Component
public class MatchEngine {
    private final TacticsRepository tactics;

    public MatchEngine(TacticsRepository tactics) { this.tactics = tactics; }

    public MatchResult play(UUID homeClubId, UUID awayClubId) {
        String home = tactics.findById(homeClubId).map(Tactics::getMentality).orElse("BALANCED");
        String away = tactics.findById(awayClubId).map(Tactics::getMentality).orElse("BALANCED");
        int homeGoals = score(home, away);
        int awayGoals = score(away, home);
        return new MatchResult(homeClubId, awayClubId, homeGoals, awayGoals);
    }

    private int score(String own, String opponent) {
        int base = switch (own) { case "ATTACKING" -> 2; case "DEFENSIVE" -> 0; default -> 1; };
        return opponent.equals("DEFENSIVE") ? Math.max(0, base - 1) : base;
    }

    public record MatchResult(UUID home, UUID away, int homeGoals, int awayGoals) {}
}
