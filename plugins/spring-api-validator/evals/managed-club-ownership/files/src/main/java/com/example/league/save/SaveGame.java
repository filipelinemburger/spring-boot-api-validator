package com.example.league.save;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;

@Entity
public class SaveGame {
    @Id
    private UUID id;
    private UUID userId;
    /** The one club this save's manager controls. Every other club is run by the AI. */
    private UUID managedClubId;
    private int seasonYear;

    protected SaveGame() {}

    public UUID getId() { return id; }
    public UUID getUserId() { return userId; }
    public UUID getManagedClubId() { return managedClubId; }
    public int getSeasonYear() { return seasonYear; }
}
