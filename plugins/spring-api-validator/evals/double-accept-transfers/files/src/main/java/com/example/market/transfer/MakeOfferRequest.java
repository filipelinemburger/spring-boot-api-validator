package com.example.market.transfer;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.math.BigDecimal;
import java.util.UUID;

public record MakeOfferRequest(
        @NotNull UUID buyerClubId,
        @NotNull UUID playerId,
        @NotNull @Positive BigDecimal amount,
        @NotNull @Positive BigDecimal wage,
        @NotNull @Min(1) @Max(5) Integer contractYears) {}
