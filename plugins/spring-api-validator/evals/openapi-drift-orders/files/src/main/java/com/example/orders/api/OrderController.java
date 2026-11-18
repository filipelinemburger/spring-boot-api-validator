package com.example.orders.api;

import com.example.orders.domain.Order;
import com.example.orders.domain.OrderRepository;
import com.example.orders.domain.OrderStatus;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/v1/orders")
public class OrderController {
    private final OrderRepository orders;

    public OrderController(OrderRepository orders) { this.orders = orders; }

    @PostMapping
    @Transactional
    public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request) {
        Order order = new Order("ORD-" + UUID.randomUUID().toString().substring(0, 8), request.customerId(),
                request.shippingAddress(), request.items().stream().map(OrderLine::sku).toList());
        return ResponseEntity.ok(OrderResponse.from(orders.save(order)));
    }

    @GetMapping("/{id}")
    @Transactional(readOnly = true)
    public OrderResponse get(@PathVariable Long id) {
        return OrderResponse.from(orders.findById(id).orElseThrow());
    }

    @Operation(summary = "Change an order's status")
    @ApiResponse(responseCode = "204", description = "Status changed")
    @PatchMapping("/{id}/status")
    @Transactional
    public OrderResponse changeStatus(@PathVariable Long id, @Valid @RequestBody UpdateStatusRequest request) {
        Order order = orders.findById(id).orElseThrow();
        order.setStatus(request.status());
        return OrderResponse.from(order);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        orders.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
