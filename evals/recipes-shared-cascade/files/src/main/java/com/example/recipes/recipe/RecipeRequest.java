package com.example.recipes.recipe;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record RecipeRequest(
        @NotBlank @Size(max = 120) String title,
        @NotBlank @Size(max = 8000) String body,
        @NotNull Long cuisineId) {
}
