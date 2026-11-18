package com.example.notes.common;

public record ApiError(String error, String message, int status) {}
