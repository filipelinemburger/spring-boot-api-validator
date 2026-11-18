package com.example.league.season;

import java.util.UUID;

public record SeasonResponse(int seasonYear, UUID competitionId, String competitionName, String champion,
                             Integer managedClubPosition) {
    static SeasonResponse from(SeasonArchive a) {
        return new SeasonResponse(a.getSeasonYear(), a.getCompetitionId(), a.getCompetitionName(),
                a.getChampionName(), a.getManagedClubPosition());
    }
}
