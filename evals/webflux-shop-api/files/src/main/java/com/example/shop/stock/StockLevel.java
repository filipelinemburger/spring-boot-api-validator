package com.example.shop.stock;

import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.Table;

@Table("stock_levels")
public record StockLevel(@Id Long id, String sku, int onHand, int reserved) {
    public StockLevel reserve(int quantity) {
        return new StockLevel(id, sku, onHand, reserved + quantity);
    }

    public int available() { return onHand - reserved; }
}
