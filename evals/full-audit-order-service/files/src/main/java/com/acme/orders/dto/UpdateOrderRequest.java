package com.acme.orders.dto;

import lombok.Data;

@Data
public class UpdateOrderRequest {
    private String shippingAddress;
    private String internalNotes;
}
