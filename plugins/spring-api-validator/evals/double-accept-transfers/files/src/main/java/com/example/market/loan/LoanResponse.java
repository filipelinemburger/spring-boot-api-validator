package com.example.market.loan;

import java.util.UUID;

public record LoanResponse(UUID id, UUID playerId, int ownerWageShare) {
    static LoanResponse from(Loan l) {
        return new LoanResponse(l.getId(), l.getPlayerId(), l.getOwnerWageShare());
    }
}
