package com.example.catalog.product;

import java.time.LocalDate;
import java.util.Comparator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/** Read model loaded from the nightly catalog export. */
@Component
public class ProductStore {

    private final Map<Long, Product> products = new ConcurrentHashMap<>();

    public Mono<Product> findById(long id) {
        return Mono.justOrEmpty(products.get(id));
    }

    public Flux<Product> findAll() {
        return Flux.fromIterable(products.values()).sort(Comparator.comparingLong(Product::getId));
    }

    public Flux<Product> findByCategory(String slug) {
        return findAll().filter(p -> p.getCategorySlug().equals(slug));
    }

    public Flux<Product> releasedBetween(LocalDate from, LocalDate to) {
        return findAll().filter(p -> !p.getReleasedOn().isBefore(from) && !p.getReleasedOn().isAfter(to));
    }
}
