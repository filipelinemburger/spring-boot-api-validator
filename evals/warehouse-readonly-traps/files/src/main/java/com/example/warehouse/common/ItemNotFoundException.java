package com.example.warehouse.common;

public class ItemNotFoundException extends RuntimeException {
    public ItemNotFoundException(Long id) {
        super("Item " + id + " not found");
    }
}
