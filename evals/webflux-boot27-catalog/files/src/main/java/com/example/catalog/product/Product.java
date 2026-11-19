package com.example.catalog.product;

import java.math.BigDecimal;
import java.time.LocalDate;

public class Product {

    private final long id;
    private final String name;
    private final String categorySlug;
    private final BigDecimal price;
    private final LocalDate releasedOn;

    public Product(long id, String name, String categorySlug, BigDecimal price, LocalDate releasedOn) {
        this.id = id;
        this.name = name;
        this.categorySlug = categorySlug;
        this.price = price;
        this.releasedOn = releasedOn;
    }

    public long getId() { return id; }
    public String getName() { return name; }
    public String getCategorySlug() { return categorySlug; }
    public BigDecimal getPrice() { return price; }
    public LocalDate getReleasedOn() { return releasedOn; }
}
