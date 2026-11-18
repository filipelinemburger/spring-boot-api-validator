package com.example.notes.common;

import org.springframework.http.HttpStatus;

public enum ErrorCode {
    EMAIL_TAKEN(HttpStatus.CONFLICT),
    INVALID_CREDENTIALS(HttpStatus.UNAUTHORIZED),
    NOTEBOOK_NOT_FOUND(HttpStatus.NOT_FOUND),
    NOTE_NOT_FOUND(HttpStatus.NOT_FOUND),
    NOTEBOOK_FULL(HttpStatus.UNPROCESSABLE_CONTENT),
    VALIDATION_ERROR(HttpStatus.BAD_REQUEST);

    private final HttpStatus status;
    ErrorCode(HttpStatus status) { this.status = status; }
    public HttpStatus status() { return status; }
}
