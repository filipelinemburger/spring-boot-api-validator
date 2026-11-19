package com.example.recipes.recipe;

import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RecipeRepository extends JpaRepository<Recipe, Long> {

    List<Recipe> findByCuisineIdOrderByIdDesc(Long cuisineId, Pageable page);

    List<Recipe> findAllByOrderByIdDesc(Pageable page);
}
