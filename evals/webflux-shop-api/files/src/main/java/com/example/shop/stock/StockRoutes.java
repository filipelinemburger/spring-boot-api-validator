package com.example.shop.stock;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.ServerResponse;

import static org.springframework.web.reactive.function.server.RouterFunctions.route;

@Configuration
public class StockRoutes {

    @Bean
    RouterFunction<ServerResponse> stockRouter(StockHandler handler) {
        return route()
                .GET("/api/stock/{sku}", handler::get)
                .POST("/api/stock/{sku}/reservations", handler::reserve)
                .build();
    }
}
