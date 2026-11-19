package com.example.catalog.category;

public class Category {

    private final String slug;
    private final String title;

    public Category(String slug, String title) {
        this.slug = slug;
        this.title = title;
    }

    public String getSlug() { return slug; }
    public String getTitle() { return title; }
}
