package com.acme.orders.dto;

import java.math.BigDecimal;

public record RefundResponse(Long id, Long orderId, BigDecimal amount, String reason) {
}
