package com.example.recipes.recipe;

import com.example.recipes.author.CurrentAuthor;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/recipes")
public class RecipeController {

    private final RecipeService service;
    private final CurrentAuthor currentAuthor;

    public RecipeController(RecipeService service, CurrentAuthor currentAuthor) {
        this.service = service;
        this.currentAuthor = currentAuthor;
    }

    @GetMapping
    public List<RecipeResponse> list(@RequestParam(required = false) Long cuisineId,
                                     @RequestParam(defaultValue = "0") @Min(0) int page,
                                     @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return service.list(cuisineId, page, size);
    }

    @GetMapping("/{id}")
    public RecipeResponse get(@PathVariable Long id) {
        return service.get(id);
    }

    @PostMapping
    public ResponseEntity<RecipeResponse> create(@Valid @RequestBody RecipeRequest request) {
        RecipeResponse created = service.create(currentAuthor.get(), request);
        return ResponseEntity.created(URI.create("/api/recipes/" + created.id())).body(created);
    }

    @PutMapping("/{id}")
    public RecipeResponse update(@PathVariable Long id, @Valid @RequestBody RecipeRequest request) {
        return service.update(currentAuthor.get(), id, request);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(currentAuthor.get(), id);
        return ResponseEntity.noContent().build();
    }
}
