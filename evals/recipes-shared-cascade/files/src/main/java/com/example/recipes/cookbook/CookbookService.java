package com.example.recipes.cookbook;

import com.example.recipes.author.Author;
import com.example.recipes.common.ForbiddenException;
import com.example.recipes.common.NotFoundException;
import com.example.recipes.recipe.Recipe;
import com.example.recipes.recipe.RecipeRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class CookbookService {

    private final CookbookRepository cookbooks;
    private final RecipeRepository recipes;

    public CookbookService(CookbookRepository cookbooks, RecipeRepository recipes) {
        this.cookbooks = cookbooks;
        this.recipes = recipes;
    }

    @Transactional(readOnly = true)
    public List<CookbookResponse> mine(Author owner) {
        return cookbooks.findByOwnerIdOrderByName(owner.getId()).stream().map(CookbookResponse::from).toList();
    }

    public CookbookResponse create(Author owner, CookbookRequest request) {
        return CookbookResponse.from(cookbooks.save(new Cookbook(request.name(), owner)));
    }

    public CookbookResponse addRecipe(Author owner, Long cookbookId, Long recipeId) {
        Cookbook cookbook = owned(owner, cookbookId);
        Recipe recipe = recipes.findById(recipeId)
                .orElseThrow(() -> new NotFoundException("Recipe " + recipeId + " not found"));
        cookbook.getRecipes().add(recipe);
        return CookbookResponse.from(cookbook);
    }

    public CookbookResponse removeRecipe(Author owner, Long cookbookId, Long recipeId) {
        Cookbook cookbook = owned(owner, cookbookId);
        cookbook.getRecipes().removeIf(r -> r.getId().equals(recipeId));
        return CookbookResponse.from(cookbook);
    }

    public void delete(Author owner, Long cookbookId) {
        cookbooks.delete(owned(owner, cookbookId));
    }

    private Cookbook owned(Author owner, Long cookbookId) {
        Cookbook cookbook = cookbooks.findById(cookbookId)
                .orElseThrow(() -> new NotFoundException("Cookbook " + cookbookId + " not found"));
        if (!cookbook.getOwner().getId().equals(owner.getId())) {
            throw new ForbiddenException("Not your cookbook");
        }
        return cookbook;
    }
}
