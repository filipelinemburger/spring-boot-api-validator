package com.example.recipes.recipe;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Reference data, seeded by data.sql. */
@Entity
@Table(name = "cuisines")
public class Cuisine {

    @Id
    private Long id;

    @Column(nullable = false, unique = true, length = 40)
    private String name;

    protected Cuisine() {
    }

    public Long getId() { return id; }
    public String getName() { return name; }
}
