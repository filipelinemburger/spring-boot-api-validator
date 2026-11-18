package com.example.market.loan;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

@Entity
@Table(name = "loans")
public class Loan {
    @Id
    private UUID id;
    private UUID playerId;
    private UUID ownerClubId;
    private UUID borrowerClubId;
    private int ownerWageShare;
    private boolean mayRecall;

    protected Loan() {}

    public Loan(UUID playerId, UUID ownerClubId, UUID borrowerClubId, int ownerWageShare, boolean mayRecall) {
        this.id = UUID.randomUUID();
        this.playerId = playerId;
        this.ownerClubId = ownerClubId;
        this.borrowerClubId = borrowerClubId;
        this.ownerWageShare = ownerWageShare;
        this.mayRecall = mayRecall;
    }

    public UUID getId() { return id; }
    public UUID getPlayerId() { return playerId; }
    public int getOwnerWageShare() { return ownerWageShare; }
}
