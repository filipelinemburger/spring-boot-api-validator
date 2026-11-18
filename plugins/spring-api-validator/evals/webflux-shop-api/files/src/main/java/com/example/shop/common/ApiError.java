package com.example.shop.common;

import java.util.List;

public record ApiError(int status, String message, List<String> errors) {}
