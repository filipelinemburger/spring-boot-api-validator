package com.example.market.transfer;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface TransferOfferRepository extends JpaRepository<TransferOffer, UUID> {
    List<TransferOffer> findByBuyerClubIdOrderByStatus(UUID buyerClubId);
}
