package com.example.market.transfer;

import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;

/** The selling AI club accepts at or above market value, counters within 25% below it, rejects lower bids. */
@Component
public class Negotiator {
    public enum Decision { ACCEPT, COUNTER, REJECT }

    public Decision respond(BigDecimal marketValue, BigDecimal bid) {
        if (bid.compareTo(marketValue) >= 0) return Decision.ACCEPT;
        if (bid.compareTo(marketValue.multiply(new BigDecimal("0.75"))) >= 0) return Decision.COUNTER;
        return Decision.REJECT;
    }

    public BigDecimal counterFor(BigDecimal marketValue) {
        return marketValue.setScale(2, RoundingMode.HALF_UP);
    }
}
