package com.example.books

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table

@Entity
@Table(name = "books")
class Book(
    @Column(length = 200) var title: String,
    @Column(length = 200) var subtitle: String?,
    @Column(length = 120) var author: String,
    @Column(length = 13) var isbn: String,
    var pages: Int,
    var stock: Int = 0,
    var reserved: Int = 0,
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) var id: Long? = null,
)
