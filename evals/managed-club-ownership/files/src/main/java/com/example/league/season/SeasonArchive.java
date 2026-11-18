package com.example.league.season;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;

/** One finished competition of one season. A season archives every competition in the save (several per year). */
@Entity
public class SeasonArchive {
    @Id
    private UUID id;
    private UUID saveId;
    private int seasonYear;
    private UUID competitionId;
    private String competitionName;
    private String championName;
    private Integer managedClubPosition;

    protected SeasonArchive() {}

    public int getSeasonYear() { return seasonYear; }
    public UUID getCompetitionId() { return competitionId; }
    public String getCompetitionName() { return competitionName; }
    public String getChampionName() { return championName; }
    public Integer getManagedClubPosition() { return managedClubPosition; }
}
