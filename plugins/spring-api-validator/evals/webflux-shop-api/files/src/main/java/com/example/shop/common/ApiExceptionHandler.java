package com.example.shop.common;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.support.WebExchangeBindException;

import java.util.List;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ApiError> notFound(NotFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ApiError(404, e.getMessage(), List.of()));
    }

    @ExceptionHandler(WebExchangeBindException.class)
    public ResponseEntity<ApiError> invalid(WebExchangeBindException e) {
        List<String> errors = e.getFieldErrors().stream().map(f -> f.getField() + " " + f.getDefaultMessage()).toList();
        return ResponseEntity.badRequest().body(new ApiError(400, "Validation failed", errors));
    }
}
