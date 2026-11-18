# OpenAPI / Swagger contract

Read when the project publishes a spec (an `openapi*.yaml`/`json`, `swagger*.json`, or any YAML/JSON whose first key is `openapi:`/`swagger:`) or documents its API with springdoc annotations (`@Operation`, `@ApiResponse`, `@Schema`). Clients — front-ends, mobile apps, generated SDKs — are built from that contract, so a drift between it and the code breaks them even when the code is internally fine.

## The mechanical comparisons
List the spec's `paths` × methods and match each to a handler, normalising path-variable names and base paths (spec `servers[0].url` / Swagger `basePath` vs `server.servlet.context-path`):
- documented operation with no handler → Error (clients get 404/405); handler not in the spec → Suggestion.
- documented 2xx status ≠ what the handler returns (`ResponseEntity.ok` vs a documented 201) → Warning.
- field in the request schema's `required` list not enforced by the DTO (no `@NotNull`/`@NotBlank`/`@NotEmpty`, or a Java primitive) → Warning; enforced but undocumented → Suggestion.
- property names that differ between schema and DTO JSON (after `@JsonProperty` and a global naming strategy), and clear type contradictions (spec `string` vs Java `int`) → Warning; undocumented DTO fields → Suggestion.
- springdoc annotations contradicting the code: `@ApiResponse(responseCode = "204")` on a handler returning 200, `@Schema(requiredMode = REQUIRED)` on an unchecked field.

## Beyond operations, statuses and names
- **Documented error responses vs real behaviour**: a documented `404` where the handler uses a bare `orElseThrow()` (really 500), a documented `400` where the body isn't validated, a documented `409` nothing produces. These are Warnings (the contract lies about failure modes clients handle).
- **Constraints**: spec `maxLength`/`minimum`/`enum`/`pattern` vs the DTO's `@Size`/`@Min`/enum type/`@Pattern` — a spec limit the code doesn't enforce (or a code limit stricter than the spec) means valid-per-spec requests get rejected or invalid ones accepted.
- **Harder shapes**: `oneOf`/`anyOf`, polymorphism (`discriminator`), wrapped responses (`Page`, envelopes), `nullable`, date formats, enum value casing.
- **Which side is right**: report the drift and say which is likely correct when the code or history makes it clear (a spec the team publishes to clients is usually the contract to keep; a stale spec should be regenerated). Don't silently pick one.

## Severity
- Error: documented operation missing; a documented required field the server rejects or a response field clients depend on that never arrives, when the spec is published to clients.
- Warning: status or field-name/type drift, unenforced documented constraints, documented error responses that don't happen.
- Suggestion: undocumented endpoints or fields, documentation gaps.

## springdoc without a spec file
When the spec is generated (`springdoc-openapi`) there's no file to compare, but the annotations are the contract: check `@ApiResponse` codes, `@Schema(requiredMode, example, allowableValues)` and `@Parameter(required)` against what the code does, as for a spec file.
