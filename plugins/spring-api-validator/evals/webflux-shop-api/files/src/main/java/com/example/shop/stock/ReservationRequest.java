package com.example.shop.stock;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

public record ReservationRequest(@NotBlank String orderId, @Positive int quantity) {}
