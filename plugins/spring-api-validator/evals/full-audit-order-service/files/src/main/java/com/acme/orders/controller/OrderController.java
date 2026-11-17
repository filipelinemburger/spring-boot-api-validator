package com.acme.orders.controller;

import com.acme.orders.dto.*;
import com.acme.orders.model.Order;
import com.acme.orders.model.OrderStatus;
import com.acme.orders.repository.OrderRepository;
import com.acme.orders.service.OrderService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/orders")
public class OrderController {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private OrderService orderService;

    @GetMapping("/getOrders")
    public List<Order> getOrders(@RequestParam(required = false) int page) {
        return orderRepository.findAll();
    }

    @GetMapping("/{id}")
    public Order getOrder(@PathVariable Long id) {
        return orderRepository.findById(id).get();
    }

    @GetMapping("/{id}/details")
    public OrderDetails getOrderDetails(@PathVariable Long id) {
        return orderService.getDetails(id);
    }

    @GetMapping("/by-date")
    public List<Order> getByDate(@RequestParam LocalDate date) {
        return orderRepository.findByOrderDate(date);
    }

    @RequestMapping("/search")
    public List<Order> search(@RequestParam OrderStatus status) {
        return orderRepository.findByStatus(status);
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody CreateOrderRequest request) {
        return ResponseEntity.ok(orderService.create(request));
    }

    @PostMapping("/{id}")
    public Order updateOrder(@PathVariable Long id, @RequestBody UpdateOrderRequest request) {
        Order order = orderRepository.findById(id).get();
        order.setShippingAddress(request.getShippingAddress());
        order.setInternalNotes(request.getInternalNotes());
        return orderRepository.save(order);
    }

    @PutMapping("/{id}")
    public Order replaceOrder(@PathVariable Long id, @RequestBody Order body) {
        Order order = orderRepository.findById(id).get();
        if (body.getShippingAddress() != null) {
            order.setShippingAddress(body.getShippingAddress());
        }
        if (body.getStatus() != null) {
            order.setStatus(body.getStatus());
        }
        return orderRepository.save(order);
    }

    @GetMapping("/{id}/cancel")
    public Order cancelOrder(@PathVariable Long id) {
        return orderService.cancel(id);
    }

    @PatchMapping("/{id}/status")
    public Order changeStatus(@PathVariable Long id, @RequestBody @jakarta.validation.Valid OrderStatusRequest request) {
        return orderService.changeStatus(id, request.status());
    }

    @PostMapping("/{id}/refunds")
    public ResponseEntity<RefundResponse> refund(@PathVariable Long id,
                                                 @RequestBody @jakarta.validation.Valid RefundRequest request) {
        RefundResponse refund = orderService.refund(id, request);
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{refundId}").buildAndExpand(refund.id()).toUri();
        return ResponseEntity.created(location).body(refund);
    }

    @DeleteMapping("/{orderId}")
    public void deleteOrder(@PathVariable Long id) {
        orderRepository.deleteById(id);
    }
}
