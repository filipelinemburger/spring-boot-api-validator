package com.example.orders.api;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

public record CreateOrderRequest(
        @NotNull Long customerId,
        @Size(max = 200) String shippingAddress,
        @NotEmpty List<@Valid OrderLine> items) {}
