package com.example.catalog.common;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(long id) {
        super("Product " + id + " not found");
    }
}
