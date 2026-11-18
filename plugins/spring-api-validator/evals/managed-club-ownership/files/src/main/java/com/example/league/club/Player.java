package com.example.league.club;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
public class Player {
    @Id
    private UUID id;
    private UUID saveId;
    private UUID clubId;
    private String name;
    private String position;
    private int overall;
    private boolean youthProspect;
    private BigDecimal wage;
    private int contractYears;

    protected Player() {}

    public UUID getId() { return id; }
    public UUID getSaveId() { return saveId; }
    public UUID getClubId() { return clubId; }
    public String getName() { return name; }
    public String getPosition() { return position; }
    public int getOverall() { return overall; }
    public boolean isYouthProspect() { return youthProspect; }
    public BigDecimal getWage() { return wage; }

    public void setClubId(UUID clubId) { this.clubId = clubId; }
    public void promote(BigDecimal wage, int contractYears) {
        this.youthProspect = false;
        this.wage = wage;
        this.contractYears = contractYears;
    }
}
