package com.example.league.staff;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record HireRequest(@NotBlank @Size(max = 80) String name, @NotNull @Min(1) @Max(20) Integer rating) {}
