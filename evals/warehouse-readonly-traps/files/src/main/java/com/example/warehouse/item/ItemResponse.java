package com.example.warehouse.item;

import java.math.BigDecimal;

public record ItemResponse(Long id, String sku, String name, BigDecimal price, String currency, int stock) {

    static ItemResponse from(Item item) {
        return new ItemResponse(item.getId(), item.getSku(), item.getName(), item.getPrice(),
                item.getCurrency(), item.getStock());
    }
}
