package com.example.recipes.recipe;

public record RecipeResponse(Long id, String title, String body, String author, String cuisine) {

    public static RecipeResponse from(Recipe r) {
        return new RecipeResponse(r.getId(), r.getTitle(), r.getBody(), r.getAuthor().getDisplayName(),
                r.getCuisine().getName());
    }
}
