package com.example.market.loan;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

import java.util.UUID;

public record LoanRequest(
        @NotNull UUID borrowerClubId,
        @NotNull UUID playerId,
        @Min(0) @Max(100) int ownerWageShare,
        boolean mayRecall) {}
