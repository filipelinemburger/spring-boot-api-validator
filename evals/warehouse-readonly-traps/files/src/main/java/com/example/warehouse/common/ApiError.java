package com.example.warehouse.common;

import java.util.List;

public record ApiError(int status, String message, List<String> details) {
}
