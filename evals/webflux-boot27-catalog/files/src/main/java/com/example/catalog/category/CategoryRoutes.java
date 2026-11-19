package com.example.catalog.category;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

@Configuration
public class CategoryRoutes {

    @Bean
    RouterFunction<ServerResponse> categoryRouter(CategoryHandler handler) {
        return RouterFunctions.route()
                .GET("/api/categories/{slug}", handler::get)
                .GET("/api/categories/{slug}/products", handler::products)
                .build();
    }
}
