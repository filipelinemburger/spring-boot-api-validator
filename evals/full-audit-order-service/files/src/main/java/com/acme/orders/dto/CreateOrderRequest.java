package com.acme.orders.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
public class CreateOrderRequest {
    @NotBlank
    private Long customerId;

    @NotNull
    private String shippingAddress;

    @NotEmpty
    private List<OrderItemRequest> items;

    private double total;
}
