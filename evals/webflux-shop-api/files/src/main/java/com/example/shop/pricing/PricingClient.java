package com.example.shop.pricing;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/** Calls the pricing service for the current customer price of a SKU. */
@Component
public class PricingClient {
    private final WebClient client;

    public PricingClient(WebClient.Builder builder, @Value("${pricing.base-url}") String baseUrl) {
        this.client = builder.baseUrl(baseUrl).build();
    }

    public Mono<PriceQuote> quote(String sku) {
        return client.get().uri("/quotes/{sku}", sku).retrieve().bodyToMono(PriceQuote.class);
    }
}
