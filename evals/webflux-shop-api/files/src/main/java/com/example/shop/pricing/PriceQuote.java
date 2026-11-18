package com.example.shop.pricing;

import java.math.BigDecimal;

public record PriceQuote(String sku, BigDecimal price, String currency) {}
