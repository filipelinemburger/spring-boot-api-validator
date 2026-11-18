package com.example.books

import org.springframework.data.domain.Page
import org.springframework.data.domain.PageRequest
import org.springframework.data.repository.findByIdOrNull
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.web.server.ResponseStatusException

@Service
class BookService(private val books: BookRepository) {

    @Transactional(readOnly = true)
    fun search(author: String, page: Int): Page<BookResponse> =
        books.findByAuthorContainingIgnoreCase(author, PageRequest.of(page, 20)).map { it.toResponse() }

    @Transactional(readOnly = true)
    fun get(id: Long): BookResponse = books.findByIdOrNull(id)!!.toResponse()

    @Transactional
    fun create(request: CreateBookRequest): BookResponse {
        if (books.existsByIsbn(request.isbn)) {
            throw ResponseStatusException(HttpStatus.CONFLICT, "ISBN already exists")
        }
        val book = Book(request.title, request.subtitle, request.author, request.isbn, request.pages)
        return books.save(book).toResponse()
    }

    @Transactional
    fun updateStock(id: Long, request: UpdateStockRequest): BookResponse {
        val book = books.findByIdOrNull(id) ?: throw ResponseStatusException(HttpStatus.NOT_FOUND, "Book not found")
        book.stock = request.stock
        return book.toResponse()
    }

    /** Holds one copy for a customer. */
    @Transactional
    fun reserve(id: Long): BookResponse {
        val book = books.findByIdOrNull(id) ?: throw ResponseStatusException(HttpStatus.NOT_FOUND, "Book not found")
        if (book.stock - book.reserved <= 0) {
            throw ResponseStatusException(HttpStatus.CONFLICT, "No copies available")
        }
        book.reserved += 1
        return book.toResponse()
    }

    @Transactional
    fun delete(id: Long) = books.deleteById(id)
}
