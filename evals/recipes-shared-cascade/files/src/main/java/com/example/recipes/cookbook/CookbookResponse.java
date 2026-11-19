package com.example.recipes.cookbook;

import com.example.recipes.recipe.Recipe;
import java.util.List;

public record CookbookResponse(Long id, String name, List<Long> recipeIds) {

    static CookbookResponse from(Cookbook c) {
        return new CookbookResponse(c.getId(), c.getName(), c.getRecipes().stream().map(Recipe::getId).toList());
    }
}
