# Kotlin

Read when the project has Kotlin sources. Everything in the checklist still applies; these are the Kotlin-specific differences.

## Validation
- Annotations on constructor properties target the constructor parameter by default, which Bean Validation ignores. `data class Req(@NotBlank val name: String)` is silently unchecked (**Error**); it needs `@field:NotBlank` (or `@get:`). Check every constraint and `@Valid` on a primary-constructor property.
- Non-null object types (`val name: String`, `val address: Address`): jackson-module-kotlin rejects a missing or null value with 400 (`MissingKotlinParameterException`) before validation runs — fine, but the message comes from Jackson; check the error body is still in the API's format.
- Non-null *value* types (`Int`, `Long`, `Boolean`, `Double` without a default) compile to JVM primitives: a missing one is filled with 0/false like a Java primitive, unless `FAIL_ON_NULL_FOR_PRIMITIVES` (or `FAIL_ON_MISSING_CREATOR_PROPERTIES`) is enabled. Treat them like Java primitives; confirm with a `@JsonTest` when it matters.

## Parameters and returns
- `@RequestParam(required = false) page: Int` is a primitive: absent → `IllegalStateException` 500 (**Error**). Use `page: Int?` or `defaultValue`.
- `repo.findByIdOrNull(id)!!` → `NullPointerException` 500 instead of 404; use `?: throw ResponseStatusException(HttpStatus.NOT_FOUND)` (or the project's not-found exception).
- A handler returning a nullable type (`fun get(): BookResponse?`) answers 200 with an empty body when it returns null — not 404.

## Build setup (don't flag when present)
- `jackson-module-kotlin` (data classes without default constructors need it), `kotlin-reflect`, the `kotlin("plugin.spring")` and `kotlin("plugin.jpa")` plugins (open classes, no-arg constructors for entities). The Spring Boot Gradle plugin turns on `-java-parameters` for Kotlin.
- JPA entities as `data class` are a smell (equals/hashCode over all properties, copy semantics) — Warning, not an Error, unless something triggers it.
