package com.acme.orders.service;

import com.acme.orders.dto.CreateOrderRequest;
import com.acme.orders.dto.OrderDetails;
import com.acme.orders.dto.RefundRequest;
import com.acme.orders.dto.RefundResponse;
import com.acme.orders.model.*;
import com.acme.orders.repository.OrderRepository;
import com.acme.orders.repository.RefundRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;
    private final RefundRepository refundRepository;

    @Transactional
    public Order create(CreateOrderRequest request) {
        Order order = new Order();
        order.setCustomerId(request.getCustomerId());
        order.setShippingAddress(request.getShippingAddress());
        order.setTotal(request.getTotal());
        order.setOrderDate(LocalDate.now());
        request.getItems().forEach(i -> {
            OrderItem item = new OrderItem();
            item.setSku(i.getSku());
            item.setQuantity(i.getQuantity());
            item.setPrice(i.getPrice());
            item.setOrder(order);
            order.getItems().add(item);
        });
        return orderRepository.save(order);
    }

    @Transactional
    public OrderDetails getDetails(Long id) {
        Order order = orderRepository.findById(id).orElseThrow();
        order.setLastViewedAt(LocalDateTime.now());
        return new OrderDetails(order.getId(), order.getStatus(), order.getItems().size(), order.getTotal());
    }

    @Transactional
    public Order cancel(Long id) {
        Order order = orderRepository.findById(id).orElseThrow();
        order.setStatus(OrderStatus.CANCELLED);
        return orderRepository.save(order);
    }

    @Transactional
    public Order changeStatus(Long id, OrderStatus status) {
        Order order = orderRepository.findById(id).orElseThrow();
        order.setStatus(status);
        return order;
    }

    @Transactional
    public RefundResponse refund(Long orderId, RefundRequest request) {
        Order order = orderRepository.findById(orderId).orElseThrow();
        order.setStatus(OrderStatus.REFUNDED);
        Refund refund = new Refund();
        refund.setOrderId(orderId);
        refund.setAmount(request.amount());
        refund.setReason(request.reason());
        Refund saved = refundRepository.save(refund);
        return new RefundResponse(saved.getId(), saved.getOrderId(), saved.getAmount(), saved.getReason());
    }
}
