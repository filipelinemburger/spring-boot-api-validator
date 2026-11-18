package com.example.books

import jakarta.validation.Valid
import org.springframework.data.domain.Page
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.servlet.support.ServletUriComponentsBuilder

@RestController
@RequestMapping("/api/books")
class BookController(private val service: BookService) {

    @GetMapping
    fun search(
        @RequestParam(defaultValue = "") author: String,
        @RequestParam(required = false) page: Int,
    ): Page<BookResponse> = service.search(author, page)

    @GetMapping("/{id}")
    fun get(@PathVariable id: Long): BookResponse = service.get(id)

    @PostMapping
    fun create(@Valid @RequestBody request: CreateBookRequest): ResponseEntity<BookResponse> {
        val created = service.create(request)
        val location = ServletUriComponentsBuilder.fromCurrentRequest().path("/{id}").buildAndExpand(created.id).toUri()
        return ResponseEntity.created(location).body(created)
    }

    @PutMapping("/{id}/stock")
    fun updateStock(@PathVariable id: Long, @RequestBody request: UpdateStockRequest): BookResponse =
        service.updateStock(id, request)

    @GetMapping("/{id}/reserve")
    fun reserve(@PathVariable id: Long): BookResponse = service.reserve(id)

    @DeleteMapping("/{bookId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    fun delete(@PathVariable id: Long) = service.delete(id)
}
