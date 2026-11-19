package com.example.warehouse.item;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import org.springframework.stereotype.Component;

/** Display conversion for the storefront; rates refreshed by ops. */
@Component
public class FxRates {

    private final Map<String, BigDecimal> perUsd = Map.of(
            "USD", BigDecimal.ONE,
            "EUR", new BigDecimal("0.92"),
            "GBP", new BigDecimal("0.79"));

    public boolean supports(String currency) {
        return perUsd.containsKey(currency);
    }

    public BigDecimal convert(BigDecimal amount, String from, String to) {
        BigDecimal usd = amount.divide(perUsd.get(from), 6, RoundingMode.HALF_UP);
        return usd.multiply(perUsd.get(to)).setScale(2, RoundingMode.HALF_UP);
    }
}
