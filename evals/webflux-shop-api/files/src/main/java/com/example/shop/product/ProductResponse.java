package com.example.shop.product;

import java.math.BigDecimal;

public record ProductResponse(Long id, String sku, String name, BigDecimal listPrice) {
    static ProductResponse from(Product p) {
        return new ProductResponse(p.id(), p.sku(), p.name(), p.listPrice());
    }
}
