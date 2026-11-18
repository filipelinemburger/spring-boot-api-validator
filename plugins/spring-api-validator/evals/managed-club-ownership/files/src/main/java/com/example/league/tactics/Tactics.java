package com.example.league.tactics;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.util.UUID;

@Entity
public class Tactics {
    @Id
    private UUID clubId;
    private String formation;
    private String mentality;
    private UUID captainId;

    protected Tactics() {}

    public Tactics(UUID clubId) { this.clubId = clubId; }

    public UUID getClubId() { return clubId; }
    public String getFormation() { return formation; }
    public String getMentality() { return mentality; }
    public UUID getCaptainId() { return captainId; }

    public void replace(String formation, String mentality, UUID captainId) {
        this.formation = formation;
        this.mentality = mentality;
        this.captainId = captainId;
    }
}
