# Review checklist

One line per check: what to look for → what happens at runtime → default severity (E Error, W Warning, S Suggestion). `→ file §` points to the detail; open it only to settle a finding you're unsure about (the runtime behaviour, the severity, or the right fix). Severity is a default: rate by what happens in this code today.

## HTTP methods, statuses, URIs  (→ http-methods.md)
- Classify each handler by tracing service/repository calls: read / create / replace / partial update / delete / action. Writes hide in JPA dirty checking (setters on managed entities in a non-readOnly `@Transactional`), `@Modifying` queries, events, emails, external calls.
- GET (or HEAD — it runs the GET handler) that changes state → prefetch/crawler/retry/`<img>` triggers it → **E**. Counters/`lastViewedAt` writes → W.
- `@RequestMapping` on a method without `method` → answers every verb → **E** if it writes, else W.
- PUT on a collection that creates, or a PUT that isn't idempotent → **E**. PATCH that copies every field (absent → null) → data loss **E**. PUT that merges non-null fields → W (it's PATCH).
- POST used to read, POST/GET to update or delete a known resource, verb in path (`/getX`, `/deleteX`) → W. Body on GET/DELETE → W.
- Legit, don't flag: action sub-resources via POST (`/orders/{id}/cancel`), POST search with structured criteria, client-id upsert via PUT, soft delete via DELETE, batch POST.
- Statuses: create → 201 + `Location`; DELETE → 204; missing single resource → 404 (not 200 null/empty, not 500); empty collection → 200 `[]`; conflict → 409. Plain return = 200 unless `@ResponseStatus`/`ResponseEntity`.
- Non-idempotent action with read-check-write and no `@Version`/lock/unique constraint → double submit runs twice → W (likely). A "complete" step that doesn't re-check the world still matches the stored offer (seller still owns item) → **E** if money moves. Acknowledge working sequential guards (status check → 409).

## Parameters & binding  (→ parameters.md)
- `@PathVariable` name not in the URI template → `MissingPathVariableException` → 500 **E**. Unnamed params break only without `-parameters` on Spring 6.1+ (Boot parent/Gradle plugin set it).
- `required = false` on a primitive (Java `int`, Kotlin non-null `Int`) without `defaultValue` → 500 when absent **E**.
- Missing required param → 400; wrong type → 400; enum params are case-sensitive.
- Date params without `@DateTimeFormat` (and no `spring.mvc.format.*`): ISO fails before 6.1 → W; 6.1+ falls back to ISO → S.
- Two `@RequestBody`s → **E**. Two equally specific patterns (`/{id}` vs `/{name}`) → ambiguous 500 **E**. Context/base path and `configurePathMatch` prefixes change real URLs.

## Bean Validation  (→ validation.md)
- No `spring-boot-starter-validation` → nothing validates **E**. `javax.validation` on Boot 3 / `jakarta.validation` on Boot 2 → silently ignored **E**.
- `@RequestBody` without `@Valid`/`@Validated` → constraints never run **E**. `BindingResult` param never checked → **E**.
- Nested object / list elements without `@Valid` (field or `List<@Valid T>`) → not cascaded **E**.
- Constraint on unsupported type (`@NotBlank`/`@Pattern`/`@Email` on non-String, `@Size` on number) → `UnexpectedTypeException` 500 once validation runs **E**.
- `@NotNull` on a primitive → can't fail, missing → 0/false W. Primitive in a request body without `@NotNull` wrapper → silently 0/false W.
- `null` passes every constraint except `@NotNull`/`@NotEmpty`/`@NotBlank`. Required text → `@NotBlank`.
- Limits wider than the DB column (`VARCHAR`, `NUMERIC(p,s)`, incl. values copied later into a narrower column) → DB error 500 W/E. BCrypt passwords: `@Size(max > 72)` → 500 on encode W.
- Param constraints (`@PathVariable @Min`): built in on 6.1+ (400); before 6.1 need class `@Validated` (→ `ConstraintViolationException`, 500 unless handled). Class `@Validated` on 6.1+ switches back to that path.
- Same DTO for create and partial update with `@NotNull` everywhere → W (separate DTOs or groups via `@Validated(Group)`).

## Request/response objects & Jackson  (→ dto-serialization.md)
- Entity as `@RequestBody` → mass assignment (ids, roles, status) **E**. Entity returned → W; **E** when it recurses (bidirectional), lazy-loads with open-in-view off, or leaks secrets/internal fields. Write endpoints commit before serialization fails → client sees 500 for a saved write.
- Can Jackson build the DTO? Lombok `@Builder`/`@Value` without `@Jacksonized`/no-arg ctor → 500 "Type definition error" **E**.
- Money as `double` W; huge `Long` ids for JS clients W; `LocalDateTime` for instants S; unknown JSON fields ignored by default (typos vanish).
- Global naming strategy + `@JsonProperty` override → inconsistent names W. Records + global naming on Jackson < 2.15 (Boot ≤ 3.0) → snake_case fields don't bind (likely) **E**.
- Lombok `@Data` on bidirectional entities: `toString` recurses; `hashCode` only for `Set` associations → W unless something triggers it.

## Responses & errors  (→ responses-errors.md)
- `.orElseThrow()` / `.get()` / Kotlin `!!` on a client-supplied id → unmapped exception 500 instead of 404 W (E if common path). `return null`/`Optional.empty()`/empty `Mono` → 200 empty body W.
- Custom exceptions without `@ResponseStatus`/advice mapping → 500. `DataIntegrityViolationException` → 500 (should be 409/400).
- One error format: check the advice covers framework exceptions (missing param, type mismatch, unreadable body, method validation) or extends `ResponseEntityExceptionHandler`. A catch-all turning 4xx into 500 → **E**. Stack traces/internal messages in bodies → **E**.
- `ResponseStatusException` gives ProblemDetail only with `spring.mvc.problemdetails.enabled` or a matching advice; otherwise Boot's `/error` body without the reason.
- App-wide, once: stateless token filter + `/error` not permitted → unhandled errors reach clients as 401 (check what the client does on 401) **E** (likely; confirm against a running server, not MockMvc).
- `Page<T>` returned directly → unstable JSON (warning on Spring Data 3.3+) S/W. Unbounded `findAll()` lists W.

## Structure, ownership, consistency  (→ structure.md)
- Every id in path/body scoped to the caller: top-level `requireOwned`, children filtered by parent. "Belongs to the user's scope" vs "may act on": a write with a weaker check than its siblings (save-level vs managed-club) → **E**.
- Same business rule on every path that does the same thing (caps, funds, state checks) → missing on one path W.
- Controllers doing repository work/transactions → W. Field `@Autowired` → S. `@CrossOrigin("*")` → W. Deleted user's token still valid → W.

## Stack-specific  (read only when it applies)
- Kotlin sources → `kotlin.md`. WebFlux or functional routes (`RouterFunction`, `coRouter`, WebMvc.fn) → `webflux.md`. Boot 2.x or 4.x, or any finding that depends on a version → `versions.md`.
