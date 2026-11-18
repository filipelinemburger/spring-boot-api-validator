# Responses, status codes in Spring, and error handling

## Return types

- **Plain object / `@ResponseBody`**: always 200 unless `@ResponseStatus` on the method says otherwise.
- **`ResponseEntity<T>`**: use when status or headers vary (201 + `Location`, 404 vs 200, 204). Check the statuses it builds against `http-methods.md` §5.
- **`return null`** from a handler → 200 with an empty body. For "not found" this lies to the client. Warning/Error depending on whether it's the not-found path.
- **`Optional<T>` return type** → `Optional.empty()` serializes as `null` with 200 (it is not turned into 404). Use `ResponseEntity.of(optional)` (404 when empty) or throw a not-found exception.
- **WebFlux**: `Mono.empty()` → 200 empty body, not 404. Use `switchIfEmpty(Mono.error(new ResponseStatusException(NOT_FOUND)))`.
- **Functional endpoints and `@ControllerAdvice`** — version-dependent, so check before claiming either way:
  - **WebFlux, Spring Framework 6.0+ (Boot 3+)**: `DispatcherHandler` passes errors from *every* handler, functional ones included, to `RequestMappingHandlerAdapter.handleError`, so **global** `@ControllerAdvice` exception handlers do apply to `RouterFunction` handlers. Advice scoped with `basePackages`/`assignableTypes`/`annotations` does not (there is no controller type to match).
  - **WebFlux, Spring 5.x (Boot 2.x)**: `@ControllerAdvice` covers annotated controllers only; an exception from a functional handler goes to the default error handling — usually 500.
  - **Spring MVC functional (WebMvc.fn)**: global advice applies since 5.3; scoped advice doesn't.
  - Where the advice doesn't apply, the exception needs `@ResponseStatus`/`ResponseStatusException`, or handling in the route (`onErrorResume`, `.onError(…)` on the router builder, a `HandlerFilterFunction`).
- **`void` handlers** → 200 with empty body; for DELETE/actions use `@ResponseStatus(HttpStatus.NO_CONTENT)` or `ResponseEntity.noContent().build()`.
- `ResponseEntity<?>`/`ResponseEntity<Object>` returning different body types per branch (DTO on success, `String` or `Map` on error) — untyped contract, inconsistent errors. Warning.

## Exceptions that become 500s

Unless mapped by an `@ExceptionHandler`/`@RestControllerAdvice`, `@ResponseStatus` on the exception class, or `ResponseStatusException`, any exception → **500**. Common cases to look for in handlers and the services they call:

- `optional.get()` / `orElseThrow()` with no argument → `NoSuchElementException` → 500 instead of 404.
- `repository.getReferenceById(id)` / `getOne` → `EntityNotFoundException` at first access → 500.
- `deleteById(missingId)`: Spring Data JPA 2.x throws `EmptyResultDataAccessException` → 500; Spring Data 3.x silently does nothing. Know the version before reporting.
- Custom `NotFoundException`, `BusinessException` etc. without a status mapping → 500.
- `DataIntegrityViolationException` (unique constraint, FK) → 500; usually should be 409 or 400.
- `ConstraintViolationException` from method validation via `@Validated` → 500 unless handled (see `validation.md`).
- `IllegalArgumentException`/`IllegalStateException` thrown as validation → 500.

## Global error handling

Check whether the project has a `@RestControllerAdvice`/`@ControllerAdvice`. If it does, check it against these; if not, recommend one (Warning) when there are custom exceptions or 500-prone paths.

- **One error format across the API.** Boot 3 / Spring 6: RFC 9457 `ProblemDetail` is the standard choice — enabled via `spring.mvc.problemdetails.enabled=true` or an advice extending `ResponseEntityExceptionHandler`. Exceptions such as `ResponseStatusException` *can* be rendered as ProblemDetail, but only when one of those is in place; otherwise they go through `sendError` to Boot's `/error`, whose default body omits the exception's reason unless `server.error.include-message` is changed. Check which applies before describing the error format (and before listing it under "Looks good"). Boot 2: `ProblemDetail` doesn't exist; a custom `ApiError`/`ErrorResponse` class is normal. Whatever the project uses, every handler and advice method should return it. Flag controllers that build their own `Map.of("error", ...)` or `String` errors.
- **Where unhandled exceptions end up — check this once per app.** Anything the advice doesn't handle (framework 4xx like `MissingServletRequestParameterException`, `MethodArgumentTypeMismatchException`, `HandlerMethodValidationException`, plus every unexpected runtime exception) is forwarded to Boot's `/error`. With Spring Security 6+ the ERROR dispatch is authorised too. In a **stateless setup with a custom token filter** (a `OncePerRequestFilter` that only sets `SecurityContextHolder`, no `permitAll` for `/error` or `DispatcherType.ERROR`), the error dispatch is anonymous and the client gets **401 instead of the real 400/500**. Then check the client: SPAs commonly log the user out on 401, which turns every server bug into a forced logout. Report as one cross-cutting Error (likely — MockMvc doesn't perform error dispatches, so confirm with a request against a running server). Fix: `.dispatcherTypeMatchers(DispatcherType.ERROR).permitAll()` (or permit `/error`) and handle the common framework exceptions plus a final `Exception` handler in the advice so the API's own error body is used.
- **Validation errors list the field errors** (field name + message), not just "Validation failed". Handle `MethodArgumentNotValidException`, and on 6.1+ `HandlerMethodValidationException`.
- **Framework 4xx exceptions keep their status**: an `@ExceptionHandler(Exception.class)` catch-all must not turn `HttpMessageNotReadableException`, `MissingServletRequestParameterException`, `MethodArgumentTypeMismatchException`, `HttpRequestMethodNotSupportedException`, `HttpMediaTypeNotSupportedException`, `NoResourceFoundException` (6.1+) into 500s. Extending `ResponseEntityExceptionHandler` handles them; a bare catch-all often doesn't. Error if it does.
- **No internal details**: no stack traces, exception class names, SQL, or `e.getMessage()` of unexpected exceptions in the body. Check `server.error.include-stacktrace`/`include-message`/`include-exception` aren't set to `always` outside dev profiles. Error.
- **Status codes match the exception**: not-found → 404, conflicts → 409, validation → 400; an advice returning `ResponseEntity.ok(error)` or 200 with `success: false` is an Error.
- **Logging**: unexpected exceptions logged once with the stack trace on the server side; expected 4xx not logged at ERROR.

## Try/catch inside controllers

Handlers that catch exceptions and return `ResponseEntity.ok(...)`/`badRequest().body(e.getMessage())` scatter error handling and leak messages. Warning; suggest letting exceptions propagate to the advice.

## Collections and pagination

- Endpoints returning unbounded `List<T>` from `findAll()` on tables that grow → Warning; suggest pagination.
- **Returning `Page<T>` directly**: since Spring Data 3.3, serializing `PageImpl` logs a warning that its JSON structure isn't stable; the recommended fix is `@EnableSpringDataWebSupport(pageSerializationMode = VIA_DTO)` or returning `PagedModel<T>`. Before 3.3, `Page` serializes but exposes a verbose, unstable shape (`pageable`, `sort`, …). Suggestion/Warning.
- Consistent paging parameters (`page`/`size`/`sort`) and response metadata across endpoints.

## Headers and content types

- `produces`/`consumes` only where needed (non-JSON endpoints, file uploads `multipart/form-data`, downloads with `Content-Disposition`).
- File downloads: correct `Content-Type`, `Content-Disposition`, streaming for large files (`StreamingResponseBody`/`Resource`) rather than loading into a `byte[]`.
- Caching headers / `ETag` for GETs are a suggestion for public read-heavy APIs, not a default finding.
- Optimistic locking: if entities use `@Version`, PUT/PATCH should accept the version (body field or `If-Match`) and map `OptimisticLockingFailureException` to 409/412.

## OpenAPI / springdoc agreement

If springdoc or swagger annotations exist, check they match behaviour: `@ApiResponse(responseCode = "201")` on a handler that returns 200; documented 404 that is actually a 500; documented required fields that aren't validated; operation summaries describing a different verb. Warning each (group repeats).
