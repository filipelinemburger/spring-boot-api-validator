package com.example.books

import jakarta.validation.constraints.Min
import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Positive
import jakarta.validation.constraints.Size

data class CreateBookRequest(
    @NotBlank @Size(max = 200) val title: String,
    @field:Size(max = 200) val subtitle: String? = null,
    @field:NotBlank @field:Size(max = 120) val author: String,
    @NotBlank @Size(min = 10, max = 13) val isbn: String,
    @field:Positive val pages: Int,
)

data class UpdateStockRequest(
    @field:Min(0) val stock: Int,
)

data class BookResponse(
    val id: Long,
    val title: String,
    val subtitle: String?,
    val author: String,
    val isbn: String,
    val pages: Int,
    val available: Int,
)

fun Book.toResponse() = BookResponse(
    id = id!!,
    title = title,
    subtitle = subtitle,
    author = author,
    isbn = isbn,
    pages = pages,
    available = stock - reserved,
)
