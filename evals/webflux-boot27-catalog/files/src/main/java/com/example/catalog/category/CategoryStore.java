package com.example.catalog.category;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

@Component
public class CategoryStore {

    private final Map<String, Category> categories = new ConcurrentHashMap<>();

    public Mono<Category> findBySlug(String slug) {
        return Mono.justOrEmpty(categories.get(slug));
    }
}
