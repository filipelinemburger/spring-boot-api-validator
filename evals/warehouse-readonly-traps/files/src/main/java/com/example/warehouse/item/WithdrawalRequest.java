package com.example.warehouse.item;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

/** Goods picked for an order. */
public record WithdrawalRequest(@NotNull @Positive Integer quantity) {
}
