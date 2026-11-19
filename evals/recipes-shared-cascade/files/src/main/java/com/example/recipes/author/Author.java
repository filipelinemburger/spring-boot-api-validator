package com.example.recipes.author;

import com.example.recipes.recipe.Recipe;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "authors")
public class Author {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 64)
    private String subject;

    @Column(name = "display_name", nullable = false, length = 80)
    private String displayName;

    /** An author's recipes go with the account. */
    @OneToMany(mappedBy = "author", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Recipe> recipes = new ArrayList<>();

    protected Author() {
    }

    public Author(String subject, String displayName) {
        this.subject = subject;
        this.displayName = displayName;
    }

    public Long getId() { return id; }
    public String getSubject() { return subject; }
    public String getDisplayName() { return displayName; }
    public List<Recipe> getRecipes() { return recipes; }
}
