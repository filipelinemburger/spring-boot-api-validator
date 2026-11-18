package com.example.books

import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.data.jpa.repository.JpaRepository

interface BookRepository : JpaRepository<Book, Long> {
    fun findByAuthorContainingIgnoreCase(author: String, pageable: Pageable): Page<Book>
    fun existsByIsbn(isbn: String): Boolean
}
