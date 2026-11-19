package com.example.recipes.author;

import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/account")
public class AccountController {

    private final CurrentAuthor currentAuthor;
    private final AuthorRepository authors;

    public AccountController(CurrentAuthor currentAuthor, AuthorRepository authors) {
        this.currentAuthor = currentAuthor;
        this.authors = authors;
    }

    /** GDPR erasure: removes the account and everything the author created. */
    @DeleteMapping
    @Transactional
    public ResponseEntity<Void> deleteAccount() {
        authors.delete(currentAuthor.get());
        return ResponseEntity.noContent().build();
    }
}
