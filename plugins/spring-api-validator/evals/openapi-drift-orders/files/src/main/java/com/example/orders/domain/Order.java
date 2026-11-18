package com.example.orders.domain;

import jakarta.persistence.*;

import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String number;
    private Long customerId;
    private String shippingAddress;
    @Enumerated(EnumType.STRING)
    private OrderStatus status = OrderStatus.NEW;
    @ElementCollection
    private List<String> skus = new ArrayList<>();

    protected Order() {}

    public Order(String number, Long customerId, String shippingAddress, List<String> skus) {
        this.number = number;
        this.customerId = customerId;
        this.shippingAddress = shippingAddress;
        this.skus = new ArrayList<>(skus);
    }

    public Long getId() { return id; }
    public String getNumber() { return number; }
    public Long getCustomerId() { return customerId; }
    public String getShippingAddress() { return shippingAddress; }
    public OrderStatus getStatus() { return status; }
    public List<String> getSkus() { return skus; }
    public void setStatus(OrderStatus status) { this.status = status; }
}
