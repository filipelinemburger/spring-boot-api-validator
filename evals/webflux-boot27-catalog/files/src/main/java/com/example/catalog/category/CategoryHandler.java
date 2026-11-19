package com.example.catalog.category;

import com.example.catalog.common.CategoryNotFoundException;
import com.example.catalog.product.Product;
import com.example.catalog.product.ProductStore;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

@Component
public class CategoryHandler {

    private final CategoryStore categories;
    private final ProductStore products;

    public CategoryHandler(CategoryStore categories, ProductStore products) {
        this.categories = categories;
        this.products = products;
    }

    public Mono<ServerResponse> get(ServerRequest request) {
        String slug = request.pathVariable("slug");
        return categories.findBySlug(slug)
                .switchIfEmpty(Mono.error(new CategoryNotFoundException(slug)))
                .flatMap(category -> ServerResponse.ok().bodyValue(category));
    }

    public Mono<ServerResponse> products(ServerRequest request) {
        String slug = request.pathVariable("slug");
        return categories.findBySlug(slug)
                .switchIfEmpty(Mono.error(new CategoryNotFoundException(slug)))
                .flatMap(category -> ServerResponse.ok().body(products.findByCategory(slug), Product.class));
    }
}
