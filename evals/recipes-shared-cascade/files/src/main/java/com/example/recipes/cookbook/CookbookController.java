package com.example.recipes.cookbook;

import com.example.recipes.author.CurrentAuthor;
import jakarta.validation.Valid;
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
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/cookbooks")
public class CookbookController {

    private final CookbookService service;
    private final CurrentAuthor currentAuthor;

    public CookbookController(CookbookService service, CurrentAuthor currentAuthor) {
        this.service = service;
        this.currentAuthor = currentAuthor;
    }

    @GetMapping
    public List<CookbookResponse> mine() {
        return service.mine(currentAuthor.get());
    }

    @PostMapping
    public ResponseEntity<CookbookResponse> create(@Valid @RequestBody CookbookRequest request) {
        CookbookResponse created = service.create(currentAuthor.get(), request);
        return ResponseEntity.created(URI.create("/api/cookbooks/" + created.id())).body(created);
    }

    @PutMapping("/{id}/recipes/{recipeId}")
    public CookbookResponse addRecipe(@PathVariable Long id, @PathVariable Long recipeId) {
        return service.addRecipe(currentAuthor.get(), id, recipeId);
    }

    @DeleteMapping("/{id}/recipes/{recipeId}")
    public CookbookResponse removeRecipe(@PathVariable Long id, @PathVariable Long recipeId) {
        return service.removeRecipe(currentAuthor.get(), id, recipeId);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(currentAuthor.get(), id);
        return ResponseEntity.noContent().build();
    }
}
