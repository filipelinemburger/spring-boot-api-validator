package com.example.catalog.common;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Every 404 in the catalog API uses the ApiError body the storefront expects. */
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler({ProductNotFoundException.class, CategoryNotFoundException.class})
    ResponseEntity<ApiError> notFound(RuntimeException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ApiError(404, ex.getMessage()));
    }
}
