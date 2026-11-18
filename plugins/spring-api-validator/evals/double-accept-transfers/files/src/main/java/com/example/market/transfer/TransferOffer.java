package com.example.market.transfer;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "transfer_offers")
public class TransferOffer {
    @Id
    private UUID id;
    private UUID playerId;
    private UUID buyerClubId;
    private UUID sellerClubId;
    private BigDecimal amount;
    private BigDecimal counterAmount;
    private BigDecimal wage;
    private int contractYears;
    @Enumerated(EnumType.STRING)
    private OfferStatus status;

    protected TransferOffer() {}

    public TransferOffer(UUID playerId, UUID buyerClubId, UUID sellerClubId, BigDecimal amount,
                         BigDecimal wage, int contractYears) {
        this.id = UUID.randomUUID();
        this.playerId = playerId;
        this.buyerClubId = buyerClubId;
        this.sellerClubId = sellerClubId;
        this.amount = amount;
        this.wage = wage;
        this.contractYears = contractYears;
        this.status = OfferStatus.PENDING;
    }

    public UUID getId() { return id; }
    public UUID getPlayerId() { return playerId; }
    public UUID getBuyerClubId() { return buyerClubId; }
    public UUID getSellerClubId() { return sellerClubId; }
    public BigDecimal getAmount() { return amount; }
    public BigDecimal getCounterAmount() { return counterAmount; }
    public BigDecimal getWage() { return wage; }
    public int getContractYears() { return contractYears; }
    public OfferStatus getStatus() { return status; }

    public void counter(BigDecimal counterAmount) { this.counterAmount = counterAmount; this.status = OfferStatus.COUNTERED; }
    public void accept() { this.status = OfferStatus.ACCEPTED; }
    public void reject() { this.status = OfferStatus.REJECTED; }
    public void withdraw() { this.status = OfferStatus.WITHDRAWN; }
}
