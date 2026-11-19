package com.example.recipes.cookbook;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CookbookRequest(@NotBlank @Size(max = 80) String name) {
}
