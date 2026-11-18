package com.example.league.common;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

/** Domain failures carry their HTTP status; Spring renders them as ProblemDetail. */
public class ApiException extends ResponseStatusException {
    public ApiException(HttpStatus status, String reason) {
        super(status, reason);
    }

    public static ApiException notFound(String what) {
        return new ApiException(HttpStatus.NOT_FOUND, what + " not found");
    }
}
