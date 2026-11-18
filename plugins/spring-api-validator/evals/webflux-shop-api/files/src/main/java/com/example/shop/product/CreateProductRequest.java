package com.example.shop.product;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public record CreateProductRequest(
        @NotBlank @Size(max = 32) String sku,
        @NotBlank @Size(max = 120) String name,
        @NotNull @DecimalMin("0.00") BigDecimal listPrice) {}
