# Bean Validation (Jakarta / javax)

Validation bugs are usually silent: the annotations are there, the code compiles, and nothing is checked. Each rule below says how to recognise that.

## Is validation enabled at all?

- **Dependency**: since Boot 2.3, `spring-boot-starter-web` no longer includes validation. Without `spring-boot-starter-validation` (or another provider such as `hibernate-validator` on the classpath), `@Valid` does nothing. Check the build file before reporting anything else in this area; if it's missing, that's one Error covering all endpoints.
- **Namespace**: Boot 3 uses `jakarta.validation.*`; Boot 2 uses `javax.validation.*`. Annotations from the other namespace compile if that API jar is on the classpath (often pulled in transitively) but the active provider ignores them. Grep imports in DTOs and controllers for the wrong namespace.

## Triggering validation of request bodies

- `@RequestBody CreateOrderRequest req` **without `@Valid` (or `@Validated`)** → constraints on the DTO are never checked. Error. This is the single most common finding.
- With `@Valid`, failures raise `MethodArgumentNotValidException` → 400 (Spring 6.1+ may raise `HandlerMethodValidationException` when method validation applies; also 400).
- `@Valid` on a parameter followed by a `BindingResult` parameter means the handler must inspect it: if the code never checks `bindingResult.hasErrors()`, invalid input passes straight through. Error.
- `@ModelAttribute` / form objects follow the same rule.

## Nested objects and collections

- Validation does **not cascade** into nested objects unless the field is marked `@Valid`: `private AddressRequest address;` with constraints inside `AddressRequest` is unchecked without `@Valid` on the field.
- Collection elements: `private List<OrderItemRequest> items;` → elements are unchecked. Use `private List<@Valid OrderItemRequest> items;` (or `@Valid` on the field). `@NotEmpty` on the list checks only the list itself.
- `@RequestBody List<OrderItemRequest>` as the top-level body: on Spring < 6.1, `@Valid` on the parameter doesn't validate the elements; use a wrapper DTO, or class-level `@Validated` with `List<@Valid OrderItemRequest>`. On 6.1+, `@RequestBody List<@Valid OrderItemRequest>` is handled by built-in method validation. Say which applies to the project's version.

## Path variables, query params, headers

- Constraints directly on method parameters (`@PathVariable @Min(1) Long id`, `@RequestParam @Size(max = 50) String q`):
  - **Spring 6.1+ (Boot 3.2+)**: applied automatically by built-in method validation → `HandlerMethodValidationException` → 400. Class-level `@Validated` is *not* needed — and if present, the AOP proxy validates instead and throws `ConstraintViolationException`, which is a **500** unless an `@ExceptionHandler` maps it. Flag class-level `@Validated` on controllers in 6.1+ projects when no handler for `ConstraintViolationException` exists.
  - **Before 6.1**: only applied if the controller class has `@Validated`; otherwise silently ignored (Error). Failures throw `ConstraintViolationException` → **500** unless handled (Warning: needs an `@ExceptionHandler` mapping to 400).

## Constraint semantics that trip people up

- **`null` is valid for almost every constraint** except `@NotNull`/`@NotEmpty`/`@NotBlank`. `@Size(min = 1) String name`, `@Min(1) Integer qty`, `@Email String email`, `@Pattern(...) String code` all accept a missing value. If the field is required, it also needs `@NotNull` (or `@NotBlank` for strings).
- **`@NotNull` vs `@NotEmpty` vs `@NotBlank`** on a `String`: `@NotNull` accepts `""` and `"   "`; `@NotEmpty` accepts `"   "`; `@NotBlank` rejects all three. Required text fields almost always want `@NotBlank`.
- **Constraint on an unsupported type** → `UnexpectedTypeException` (HV000030) at request time → **500** for every request: `@NotBlank` / `@NotEmpty` / `@Pattern` / `@Email` on `Long`, `Integer`, `LocalDate`, enums etc.; `@Size` on a number; `@Min` on a `String` is supported by Hibernate Validator but is a smell. Error.
- **Primitives**: `@NotNull int quantity` can never fail — a missing JSON field (or explicit `null`, since Jackson's `FAIL_ON_NULL_FOR_PRIMITIVES` is off by default) becomes `0`/`false`. Required numeric/boolean fields must be wrappers (`Integer`, `Boolean`) with `@NotNull`. Also check `@Min(1) int quantity`: it does reject the silent `0`, but with a misleading message ("must be ≥ 1" instead of "required").
- `@Email` (Hibernate Validator) accepts `a@b` (no dot required). Flag only if the domain needs stricter checks.
- `@Positive`/`@PositiveOrZero`/`@DecimalMin` on `BigDecimal` money fields; `@Digits(integer, fraction)` for scale. Money without any bound is a suggestion.
- `@Past`/`@Future` on date fields where the domain implies it (birth date, scheduled date).
- **Passwords hashed with BCrypt**: BCrypt only uses 72 bytes, and since Spring Security 6.4.4 `BCryptPasswordEncoder` throws `IllegalArgumentException` for longer input. `@Size(max = 100)` on a password therefore lets 73–100-character passwords (fewer with non-ASCII characters) reach a 500. Cap at 72 bytes.
- **Numbers vs `NUMERIC(p,s)` columns** (quick-check rule QC20 lists the candidates when `scripts/` is present): amounts without `@DecimalMax`/`@Digits` overflow the column at flush. Check the *narrowest* column the value ends up in — a value accepted into a wide staging column (an offer, an agreement) and later copied into a narrower one (the player's wage) fails at that later step, possibly in a batch job such as a season rollover, every time it runs.
- `@Size(max = …)` on strings that map to bounded DB columns (`@Column(length = 100)`) — missing bounds turn oversize input into a 500 from the database instead of a 400.

## Create vs update

- Reusing one DTO for POST (create) and PATCH (partial update) with `@NotNull` on every field makes PATCH impossible to use partially, or forces the team to drop constraints and lose create validation. Look for: one DTO used by both, with constraints that only make sense for create.
- Fixes: separate DTOs (preferred, clearer), or validation groups with `@Validated(OnCreate.class)` — note that `@Valid` does not support groups; only `@Validated(...)` does.
- An `id` field in a create DTO (client-supplied id for server-generated ids) is a mass-assignment smell (see `dto-serialization.md`).

## Kotlin and functional endpoints

See `kotlin.md` (use-site targets, value types, `!!`) and `webflux.md` (functional handlers get no Bean Validation).


## Records

Constraint annotations on record components propagate to the field/accessor/constructor parameter as needed, so `record CreateUser(@NotBlank String name, @Valid AddressDto address)` works. Nothing special to flag.

## Custom validators

For custom `@Constraint` annotations, check: the `ConstraintValidator` returns `true` for `null` (convention, so it can be combined with `@NotNull`), and it doesn't do I/O-heavy work (database lookups per field) without the team being aware.
