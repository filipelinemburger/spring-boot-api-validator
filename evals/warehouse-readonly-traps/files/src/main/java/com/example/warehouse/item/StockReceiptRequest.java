package com.example.warehouse.item;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Positive;
import javax.validation.constraints.Size;

/** Goods received at the dock. */
public record StockReceiptRequest(
        @NotNull @Positive Integer quantity,
        @Size(max = 200) String note) {
}
