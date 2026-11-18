package com.acme.orders.repository;

import com.acme.orders.model.Order;
import com.acme.orders.model.OrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByOrderDate(LocalDate date);
    List<Order> findByStatus(OrderStatus status);
    List<Order> findByCustomerId(Long customerId);
}
