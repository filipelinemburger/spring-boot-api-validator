package com.example.orders.api;

import com.example.orders.domain.Order;

public record OrderResponse(Long id, String number, String status, int itemCount, String shippingAddress) {
    static OrderResponse from(Order o) {
        return new OrderResponse(o.getId(), o.getNumber(), o.getStatus().name(), o.getSkus().size(),
                o.getShippingAddress());
    }
}
