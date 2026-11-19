package com.example.catalog.product;

import com.example.catalog.common.ProductNotFoundException;
import java.time.LocalDate;
import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    private final ProductStore store;

    public ProductController(ProductStore store) {
        this.store = store;
    }

    @GetMapping
    public Flux<Product> list(@RequestParam(defaultValue = "0") @Min(0) int page,
                              @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return store.findAll().skip((long) page * size).take(size);
    }

    @GetMapping("/{id}")
    public Mono<Product> get(@PathVariable long id) {
        return store.findById(id).switchIfEmpty(Mono.error(new ProductNotFoundException(id)));
    }

    /** Release calendar for the storefront, e.g. ?from=2026-01-01&to=2026-03-31. */
    @GetMapping("/released")
    public Flux<Product> released(@RequestParam LocalDate from, @RequestParam LocalDate to) {
        return store.releasedBetween(from, to);
    }
}
