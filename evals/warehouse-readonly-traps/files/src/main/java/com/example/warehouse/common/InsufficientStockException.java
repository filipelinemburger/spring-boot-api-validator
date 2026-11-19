package com.example.warehouse.common;

public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(String sku, int available, int requested) {
        super("Only " + available + " of " + sku + " in stock, " + requested + " requested");
    }
}
