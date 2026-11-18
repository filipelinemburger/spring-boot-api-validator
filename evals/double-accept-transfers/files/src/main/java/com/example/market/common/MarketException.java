package com.example.market.common;

import org.springframework.http.HttpStatus;

public class MarketException extends RuntimeException {
    private final HttpStatus status;
    private final String code;

    public MarketException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    public HttpStatus status() { return status; }
    public String code() { return code; }
}
