package com.acme.orders.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class OrderItemRequest {
    @NotBlank
    private String sku;

    @NotNull
    private int quantity;

    @NotNull
    @Positive
    private BigDecimal price;
}
