package com.example.catalog.common;

public class CategoryNotFoundException extends RuntimeException {
    public CategoryNotFoundException(String slug) {
        super("Category '" + slug + "' not found");
    }
}
