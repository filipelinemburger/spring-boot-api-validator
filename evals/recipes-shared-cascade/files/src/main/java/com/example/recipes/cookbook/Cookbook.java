package com.example.recipes.cookbook;

import com.example.recipes.author.Author;
import com.example.recipes.recipe.Recipe;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.JoinTable;
import jakarta.persistence.ManyToMany;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.util.LinkedHashSet;
import java.util.Set;

/** A personal collection of saved recipes, from any author. */
@Entity
@Table(name = "cookbooks")
public class Cookbook {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 80)
    private String name;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "owner_id")
    private Author owner;

    @ManyToMany(cascade = CascadeType.ALL)
    @JoinTable(name = "cookbook_recipes",
            joinColumns = @JoinColumn(name = "cookbook_id"),
            inverseJoinColumns = @JoinColumn(name = "recipe_id"))
    private Set<Recipe> recipes = new LinkedHashSet<>();

    protected Cookbook() {
    }

    public Cookbook(String name, Author owner) {
        this.name = name;
        this.owner = owner;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public Author getOwner() { return owner; }
    public Set<Recipe> getRecipes() { return recipes; }
}
