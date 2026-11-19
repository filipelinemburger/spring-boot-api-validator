package com.example.recipes.recipe;

import com.example.recipes.author.Author;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "recipes")
public class Recipe {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String title;

    @Column(nullable = false, length = 8000)
    private String body;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "author_id")
    private Author author;

    @ManyToOne(cascade = CascadeType.ALL, optional = false)
    @JoinColumn(name = "cuisine_id")
    private Cuisine cuisine;

    protected Recipe() {
    }

    public Recipe(String title, String body, Author author, Cuisine cuisine) {
        this.title = title;
        this.body = body;
        this.author = author;
        this.cuisine = cuisine;
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public String getBody() { return body; }
    public Author getAuthor() { return author; }
    public Cuisine getCuisine() { return cuisine; }

    public void edit(String title, String body, Cuisine cuisine) {
        this.title = title;
        this.body = body;
        this.cuisine = cuisine;
    }
}
