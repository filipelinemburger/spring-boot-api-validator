# Request and response objects (DTOs) and Jackson

Check what actually goes over the wire, given Jackson's rules and the global `ObjectMapper` configuration. Read `spring.jackson.*` properties and any `Jackson2ObjectMapperBuilderCustomizer` / `ObjectMapper` bean first: they change several of the defaults below.

## Spring Boot's Jackson defaults (unless overridden)

- `FAIL_ON_UNKNOWN_PROPERTIES` **disabled**: unknown JSON fields are silently ignored. A client typo (`"quantitty": 3`) is dropped, and combined with a primitive field the value becomes `0`. Not a defect on its own, but mention it when a finding depends on it.
- `WRITE_DATES_AS_TIMESTAMPS` disabled: `java.time` types are written as ISO-8601 strings.
- Modules registered: JavaTimeModule, Jdk8Module (`Optional`), ParameterNamesModule, and the Kotlin module if on the classpath.
- Property naming: camelCase unless `spring.jackson.property-naming-strategy` (e.g. `SNAKE_CASE`) is set. With a global strategy, a hand-written `@JsonProperty("productName")` overrides it and breaks consistency.
- **Records + global naming strategy on Jackson < 2.15** (Boot ≤ 3.0): the strategy is not applied to record constructor parameters (jackson-databind #2992), so a snake_case request field like `category_code` is silently ignored and the component ends up `null`, while serialization uses snake_case. Mark "likely" unless you can see the resolved Jackson version, and suggest a `@JsonTest` to confirm.

## Entities vs DTOs

- **Returning JPA entities** from controllers (`ResponseEntity<Order>` where `Order` is `@Entity`). Warning by default; Error when it causes one of:
  - **Infinite recursion** on bidirectional relationships (`Order.items` ↔ `OrderItem.order`) → `JsonMappingException`/`StackOverflowError` → 500, unless `@JsonManagedReference`/`@JsonBackReference`/`@JsonIgnore` break the cycle.
  - **Lazy loading**: with `spring.jpa.open-in-view=false`, serializing a lazy association throws `LazyInitializationException` → 500; with it on (Boot's default, logs a warning), it silently triggers extra queries (N+1). Hibernate proxies may also serialize `hibernateLazyInitializer` fields or fail.
  - **Leaked fields**: password hashes, internal notes, audit columns, soft-delete flags, tenant ids.
  - **Write committed, then 500**: on POST/PUT/PATCH handlers the service transaction commits *before* the response is serialized. If serialization then fails (recursion, lazy loading), the change is saved but the client sees a 500 and may retry — duplicate creates, repeated refunds. Call this out on write endpoints that return entities.
  - **Lombok `@Data`/`@EqualsAndHashCode`/`@ToString` on bidirectional entities**: generated `hashCode`/`toString` recurse through the relationship → `StackOverflowError` as soon as the entity is logged, put in a `Set`, or compared. Also breaks Hibernate's identity semantics for `equals`. Use `@Getter`/`@Setter` and id-based `equals`, or exclude the back-reference.
  - The API shape becomes coupled to the schema: renaming a column changes the contract.
- **Accepting entities as `@RequestBody`** → **mass assignment**: the client can set `id`, `role`, `createdAt`, `ownerId`, `status`, relationships. Error when the entity has fields the client must not control (ids, roles, ownership, prices computed server-side, status).
- Suggest separate request and response DTOs (records are ideal) and a mapping layer (manual, MapStruct, etc. — follow what the codebase uses).

## Can Jackson construct the request DTO?

Deserialization needs a way to create the object:
- A no-arg constructor (+ setters or field access), a `record`, or a constructor annotated `@JsonCreator` (with `@JsonProperty` names, or `-parameters` + ParameterNamesModule).
- **Lombok `@Builder` / `@Value` alone** removes the no-arg constructor: deserialization fails with `InvalidDefinitionException: Cannot construct instance` — Spring surfaces this as `HttpMessageConversionException` ("Type definition error") → **500**. Fix: `@Jacksonized` with `@Builder`, or add `@NoArgsConstructor` + `@AllArgsConstructor`, or use a record.
- Single-argument constructors are ambiguous for Jackson (delegating vs property-based) — prefer explicit `@JsonCreator(mode = PROPERTIES)` or a record. If unsure, mark "likely" and suggest a quick `@JsonTest` or MockMvc check.
- `final` fields without a creator constructor → can't be set.
- Inner (non-static) classes can't be deserialized.

## Property names and accessors

- **Boolean naming with Lombok**: primitive `boolean active` → `isActive()` → JSON `active`; primitive `boolean isActive` → Lombok generates `isActive()` → JSON `active` (the `is` is dropped); wrapper `Boolean isActive` → `getIsActive()` → JSON `isActive`. Check the JSON name matches what the API documents and is consistent across DTOs.
- Getters without fields (`getFullName()`) are serialized — computed or internal values may leak. `@JsonIgnore` or remove.
- Field/getter mismatches (`@JsonProperty` on the field but a differently named getter) can produce duplicate properties.
- Mixed naming styles across DTOs (`customer_id` in one, `customerId` in another) — Warning for consistency.

## Types

- **Money**: `double`/`float` for amounts, prices, totals → rounding errors (`0.1 + 0.2`). Use `BigDecimal` (or minor units in `long`). Warning; Error if arithmetic on money happens in doubles.
- **Large ids**: `Long` ids above 2^53 (snowflake/TSID ids) lose precision in JavaScript clients. Warning only when ids are generated that large; suggest `@JsonSerialize(using = ToStringSerializer.class)` or string ids.
- **Dates**: `java.util.Date`/`Calendar` → prefer `java.time`. `LocalDateTime` in an API has no timezone and is ambiguous across clients; prefer `Instant`/`OffsetDateTime` for timestamps, `LocalDate` for calendar dates. `@JsonFormat` patterns should be ISO-8601 and consistent.
- **Enums**: an unknown value in a request → `HttpMessageNotReadableException` → 400 (fine). Case-sensitive by default (`ACCEPT_CASE_INSENSITIVE_ENUMS` off). Adding enum constants to a response breaks strict clients — mention for public APIs only. `@JsonValue`/`@JsonCreator` used consistently.
- **`Optional<T>` as a DTO field**: works (Jdk8Module) but is discouraged; it doesn't distinguish absent vs null on input either. Suggestion.
- `Object`/`Map<String, Object>` request bodies bypass typing and validation — Warning unless the endpoint is intentionally schemaless.
- Polymorphic `@JsonTypeInfo(use = Id.CLASS)` or default typing → deserialization of arbitrary classes, a known security risk. Error.

## Response shape

- **Nulls**: `@JsonInclude(NON_NULL)` applied in some DTOs but not others (or globally via `spring.jackson.default-property-inclusion`) — inconsistent shapes. Collections should be `[]`, not `null`.
- **Envelopes**: if the codebase wraps responses (`ApiResponse<T>{data, meta}`), every endpoint should; a bare object from one controller is a consistency Warning. Don't introduce an envelope where none exists.
- Returning `String` from a `@RestController` (e.g. `return "deleted"`) writes `text/plain`, not JSON — clients expecting JSON break. Warning.
- Returning `Map<String, Object>` built ad hoc — untyped contract, invisible to OpenAPI. Suggestion/Warning.
- Sensitive data in responses: passwords (even hashed), tokens, secrets, full card numbers, internal ids of other tenants. Error.
- Request DTOs echoed back as responses (`return request;`) — misses server-generated fields (id, timestamps). Warning.

## Structure of the DTO classes

- Request and response DTOs separate (`CreateOrderRequest`, `UpdateOrderRequest`, `OrderResponse`), named consistently with the codebase.
- Immutable where possible (records / `@Value` + `@Jacksonized`).
- No business logic or repository access inside DTOs.
- OpenAPI annotations (`@Schema(required = true)`, `requiredMode`, `example`) agree with the Bean Validation constraints and nullability — a `@Schema(requiredMode = REQUIRED)` field with no `@NotNull` is a documented contract the server doesn't enforce. Warning.
