package com.example.shop.stock;

public record StockResponse(String sku, int available) {
    static StockResponse from(StockLevel s) {
        return new StockResponse(s.sku(), s.available());
    }
}
