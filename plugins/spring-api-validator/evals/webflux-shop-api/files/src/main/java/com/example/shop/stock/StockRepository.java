package com.example.shop.stock;

import org.springframework.data.repository.reactive.ReactiveCrudRepository;
import reactor.core.publisher.Mono;

public interface StockRepository extends ReactiveCrudRepository<StockLevel, Long> {
    Mono<StockLevel> findBySku(String sku);
}
