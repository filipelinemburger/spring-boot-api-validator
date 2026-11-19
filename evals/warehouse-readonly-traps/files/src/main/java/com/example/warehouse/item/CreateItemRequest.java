package com.example.warehouse.item;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public record CreateItemRequest(
        @NotBlank @Size(max = 40) String sku,
        @NotBlank @Size(max = 120) String name,
        @NotNull @DecimalMin("0.00") @Digits(integer = 8, fraction = 2) BigDecimal price,
        @NotBlank @Pattern(regexp = "[A-Z]{3}") String currency) {
}
