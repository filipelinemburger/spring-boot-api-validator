package com.example.shop.stock;

import com.example.shop.common.NotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import reactor.core.publisher.Mono;

@Component
public class StockHandler {
    private final StockRepository stock;

    public StockHandler(StockRepository stock) { this.stock = stock; }

    public Mono<ServerResponse> get(ServerRequest request) {
        String sku = request.pathVariable("sku");
        return stock.findBySku(sku)
                .switchIfEmpty(Mono.error(new NotFoundException("No stock record for " + sku)))
                .flatMap(level -> ServerResponse.ok().bodyValue(StockResponse.from(level)));
    }

    public Mono<ServerResponse> reserve(ServerRequest request) {
        String sku = request.pathVariable("sku");
        return request.bodyToMono(ReservationRequest.class)
                .flatMap(reservation -> stock.findBySku(sku)
                        .switchIfEmpty(Mono.error(new NotFoundException("No stock record for " + sku)))
                        .flatMap(level -> level.available() < reservation.quantity()
                                ? ServerResponse.status(HttpStatus.CONFLICT).bodyValue("Not enough stock")
                                : stock.save(level.reserve(reservation.quantity()))
                                        .flatMap(saved -> ServerResponse.ok().bodyValue(StockResponse.from(saved)))));
    }
}
