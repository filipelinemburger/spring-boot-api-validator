package com.acme.catalog.web;

import com.acme.catalog.core.Category;
import com.acme.catalog.core.CategoryRepository;
import com.acme.catalog.core.NotFoundException;
import com.acme.catalog.web.dto.CategoryRequest;
import com.acme.catalog.web.dto.CategoryResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import javax.validation.Valid;
import java.net.URI;

@RestController
@RequestMapping("/api/v1/categories")
public class CategoryController {
    private final CategoryRepository categories;

    public CategoryController(CategoryRepository categories) { this.categories = categories; }

    @GetMapping("/{code}")
    public CategoryResponse get(@PathVariable String code) {
        Category c = categories.findById(code).orElseThrow(() -> new NotFoundException("category " + code));
        return new CategoryResponse(c.getCode(), c.getName());
    }

    @PostMapping
    public ResponseEntity<CategoryResponse> create(@Valid @RequestBody CategoryRequest request) {
        Category c = new Category();
        c.setCode(request.code());
        c.setName(request.name());
        categories.save(c);
        URI location = ServletUriComponentsBuilder.fromCurrentRequest().path("/{code}").buildAndExpand(c.getCode()).toUri();
        return ResponseEntity.created(location).body(new CategoryResponse(c.getCode(), c.getName()));
    }
}
