package com.example.market.club;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "players")
public class Player {
    @Id
    private UUID id;
    private UUID clubId;
    private String name;
    private BigDecimal marketValue;
    @Column(precision = 10, scale = 2)
    private BigDecimal wage;
    private int contractYears;
    private UUID onLoanFrom;

    protected Player() {}

    public UUID getId() { return id; }
    public UUID getClubId() { return clubId; }
    public String getName() { return name; }
    public BigDecimal getMarketValue() { return marketValue; }
    public BigDecimal getWage() { return wage; }
    public UUID getOnLoanFrom() { return onLoanFrom; }

    public void joinClub(UUID clubId, BigDecimal wage, int contractYears) {
        this.clubId = clubId;
        this.wage = wage;
        this.contractYears = contractYears;
    }

    public void loanTo(UUID borrowerClubId) {
        this.onLoanFrom = this.clubId;
        this.clubId = borrowerClubId;
    }
}
