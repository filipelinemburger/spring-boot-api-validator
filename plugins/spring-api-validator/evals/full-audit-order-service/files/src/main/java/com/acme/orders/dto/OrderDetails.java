package com.acme.orders.dto;

import com.acme.orders.model.OrderStatus;

public record OrderDetails(Long id, OrderStatus status, int itemCount, double total) {
}
