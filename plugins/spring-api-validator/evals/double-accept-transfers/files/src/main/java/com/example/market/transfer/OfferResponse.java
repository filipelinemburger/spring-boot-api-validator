package com.example.market.transfer;

import java.math.BigDecimal;
import java.util.UUID;

public record OfferResponse(UUID id, UUID playerId, BigDecimal amount, BigDecimal counterAmount, OfferStatus status) {
    static OfferResponse from(TransferOffer o) {
        return new OfferResponse(o.getId(), o.getPlayerId(), o.getAmount(), o.getCounterAmount(), o.getStatus());
    }
}
