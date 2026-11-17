package com.acme.catalog.web.dto;

import java.time.Instant;
import java.util.List;

public record ApiError(int status, String code, String message, List<FieldError> fieldErrors, Instant timestamp) {
    public record FieldError(String field, String message) {}
}
