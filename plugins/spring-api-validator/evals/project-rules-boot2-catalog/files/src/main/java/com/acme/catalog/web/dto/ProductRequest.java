package com.acme.catalog.web.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

import java.math.BigDecimal;

public record ProductRequest(@NotBlank String name,
                             @NotBlank String categoryCode,
                             @NotNull @PositiveOrZero BigDecimal price,
                             @PositiveOrZero Integer stock) {
}
