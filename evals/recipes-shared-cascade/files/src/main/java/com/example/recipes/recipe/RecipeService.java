package com.example.recipes.recipe;

import com.example.recipes.author.Author;
import com.example.recipes.common.ForbiddenException;
import com.example.recipes.common.NotFoundException;
import java.util.List;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class RecipeService {

    private final RecipeRepository recipes;
    private final CuisineRepository cuisines;

    public RecipeService(RecipeRepository recipes, CuisineRepository cuisines) {
        this.recipes = recipes;
        this.cuisines = cuisines;
    }

    @Transactional(readOnly = true)
    public List<RecipeResponse> list(Long cuisineId, int page, int size) {
        PageRequest pr = PageRequest.of(page, size);
        List<Recipe> found = cuisineId == null
                ? recipes.findAllByOrderByIdDesc(pr)
                : recipes.findByCuisineIdOrderByIdDesc(cuisineId, pr);
        return found.stream().map(RecipeResponse::from).toList();
    }

    @Transactional(readOnly = true)
    public RecipeResponse get(Long id) {
        return RecipeResponse.from(find(id));
    }

    public RecipeResponse create(Author author, RecipeRequest request) {
        Recipe recipe = new Recipe(request.title(), request.body(), author, cuisine(request.cuisineId()));
        return RecipeResponse.from(recipes.save(recipe));
    }

    public RecipeResponse update(Author author, Long id, RecipeRequest request) {
        Recipe recipe = owned(author, id);
        recipe.edit(request.title(), request.body(), cuisine(request.cuisineId()));
        return RecipeResponse.from(recipe);
    }

    public void delete(Author author, Long id) {
        recipes.delete(owned(author, id));
    }

    Recipe owned(Author author, Long id) {
        Recipe recipe = find(id);
        if (!recipe.getAuthor().getId().equals(author.getId())) {
            throw new ForbiddenException("Only the author can change this recipe");
        }
        return recipe;
    }

    private Recipe find(Long id) {
        return recipes.findById(id).orElseThrow(() -> new NotFoundException("Recipe " + id + " not found"));
    }

    private Cuisine cuisine(Long id) {
        return cuisines.findById(id).orElseThrow(() -> new NotFoundException("Cuisine " + id + " not found"));
    }
}
