package com.acme.catalog.web;

import com.acme.catalog.core.NotFoundException;
import com.acme.catalog.core.Product;
import com.acme.catalog.core.ProductService;
import com.acme.catalog.web.dto.ProductRequest;
import com.acme.catalog.web.dto.ProductResponse;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.Map;

@RestController
@RequestMapping("/products")
public class ProductController {
    private final ProductService productService;

    public ProductController(ProductService productService) { this.productService = productService; }

    @GetMapping("/{id}")
    public ResponseEntity<?> get(@PathVariable Long id) {
        try {
            return ResponseEntity.ok(toResponse(productService.get(id)));
        } catch (NotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping
    public Page<Product> byCategory(@RequestParam String category, Pageable pageable) {
        return productService.byCategory(category, pageable);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProductResponse create(@Valid @RequestBody ProductRequest request) {
        return toResponse(productService.create(request.name(), request.categoryCode(), request.price(), request.stock()));
    }

    @PutMapping("/{id}")
    public ProductResponse replace(@PathVariable Long id, @Valid @RequestBody ProductRequest request) {
        return toResponse(productService.replace(id, request.name(), request.categoryCode(), request.price(), request.stock()));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        productService.delete(id);
    }

    private ProductResponse toResponse(Product p) {
        return new ProductResponse(p.getId(), p.getName(), p.getCategoryCode(), p.getPrice(), p.getStock());
    }
}
