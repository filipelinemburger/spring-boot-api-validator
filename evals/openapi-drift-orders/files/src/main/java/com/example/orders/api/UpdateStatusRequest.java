package com.example.orders.api;

import com.example.orders.domain.OrderStatus;
import io.swagger.v3.oas.annotations.media.Schema;

public record UpdateStatusRequest(
        @Schema(requiredMode = Schema.RequiredMode.REQUIRED, description = "The new status")
        OrderStatus status) {}
