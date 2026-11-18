package com.example.shop.product;

import com.example.shop.pricing.PriceQuote;
import com.example.shop.pricing.PricingClient;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.net.URI;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    private final ProductRepository products;
    private final PricingClient pricing;

    public ProductController(ProductRepository products, PricingClient pricing) {
        this.products = products;
        this.pricing = pricing;
    }

    @GetMapping
    public Flux<ProductResponse> list() {
        return products.findAll().map(ProductResponse::from);
    }

    @GetMapping("/{id}")
    public Mono<ProductResponse> get(@PathVariable Long id) {
        return products.findById(id).map(ProductResponse::from);
    }

    @PostMapping
    public Mono<ResponseEntity<ProductResponse>> create(@Valid @RequestBody CreateProductRequest request) {
        return products.existsBySku(request.sku())
                .flatMap(exists -> exists
                        ? Mono.error(new ResponseStatusException(HttpStatus.CONFLICT, "SKU already exists"))
                        : products.save(new Product(null, request.sku(), request.name(), request.listPrice())))
                .map(saved -> ResponseEntity.created(URI.create("/shop/api/products/" + saved.id()))
                        .body(ProductResponse.from(saved)));
    }

    @GetMapping("/{id}/price")
    public Mono<PriceQuote> price(@PathVariable Long id) {
        return products.findById(id)
                .switchIfEmpty(Mono.error(new ResponseStatusException(HttpStatus.NOT_FOUND, "Product not found")))
                .map(product -> {
                    PriceQuote quote = pricing.quote(product.sku()).block();
                    return quote != null ? quote : new PriceQuote(product.sku(), product.listPrice(), "EUR");
                });
    }
}
