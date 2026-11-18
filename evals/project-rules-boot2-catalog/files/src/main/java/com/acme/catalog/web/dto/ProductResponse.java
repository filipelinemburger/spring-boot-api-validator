package com.acme.catalog.web.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

public record ProductResponse(Long id,
                              @JsonProperty("productName") String name,
                              String categoryCode,
                              BigDecimal price,
                              int stock) {
}
