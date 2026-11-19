package com.example.recipes.author;

import com.example.recipes.common.NotFoundException;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

@Component
public class CurrentAuthor {

    private final AuthorRepository authors;

    public CurrentAuthor(AuthorRepository authors) {
        this.authors = authors;
    }

    public Author get() {
        String subject = SecurityContextHolder.getContext().getAuthentication().getName();
        return authors.findBySubject(subject)
                .orElseThrow(() -> new NotFoundException("No author profile for this account"));
    }
}
