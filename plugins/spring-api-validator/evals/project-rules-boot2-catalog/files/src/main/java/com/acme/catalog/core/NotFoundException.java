package com.acme.catalog.core;

public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) { super(message); }
}
