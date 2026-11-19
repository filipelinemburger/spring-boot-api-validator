# Code structure of the API layer

Follow the structure the codebase already uses (package-by-feature or package-by-layer, naming suffixes, mapping approach). Flag *deviations* from it and genuine responsibility problems — don't push a different architecture.

## Controllers

- `@RestController` (or `@Controller` + `@ResponseBody`). A `@Controller` without `@ResponseBody` returning a DTO tries to resolve a view → 500/404. Error.
- Base path on the class (`@RequestMapping("/api/v1/orders")`), verb-specific annotations on methods.
- **Thin handlers**: bind input, call one service method, map the result to a response. Warning when a controller:
  - injects repositories directly and runs queries or saves (business logic and transactions belong in the service layer);
  - contains business rules, calculations, multi-step workflows, or `@Transactional`;
  - catches exceptions to build error responses (see `responses-errors.md`).
- One resource (aggregate) per controller; a controller mixing `/orders` and `/customers/{id}/invoices` is a suggestion to split.
- Handler method names describe the operation (`getOrder`, `createOrder`, `cancelOrder`) and agree with the verb — a mismatch (`deleteUser` on a `@GetMapping`) usually points to an `http-methods.md` finding.

## Dependency injection

- Constructor injection (`final` fields, Lombok `@RequiredArgsConstructor` or an explicit constructor). Field `@Autowired` is a suggestion (harder to test, hides dependencies), not a defect.
- No `new SomeService()` inside controllers.

## Services

- Transaction boundaries on service methods; read paths `@Transactional(readOnly = true)` where the codebase uses transactions. A read-only transaction also documents (and, with Hibernate, enforces flush mode) that a GET path doesn't write — useful evidence for the HTTP method check.
- Services return domain objects or DTOs consistently (follow the codebase); entity → DTO mapping happens in one place.

## DTO and mapping layer

- Request/response DTOs live in the package the codebase uses for them (`dto`, `api`, `web.model`…), separate from `@Entity` classes.
- Mapping centralised (MapStruct mapper, `toResponse()` static factories, or a mapper class) rather than duplicated across handlers.

## Resource ownership (check every id in the path and body)

For every id a handler accepts, follow it into the service and confirm it is scoped to the caller — this is where real API bugs hide in multi-user apps:
- The top-level resource belongs to the authenticated user (a `requireOwned(id, userId)`-style check, answering 404 for someone else's).
- Each child id (`{clubId}`, `{offerId}`, a `playerId` in the body) belongs to *that* parent — filtered by the parent id, not just loaded by id.
- **"Belongs to" vs "may act on"**: in a write path, being inside the caller's scope may not be enough. If the domain distinguishes the thing the user controls (their managed club, their own account, their team) from other things in the same scope, writes must check the narrower one. Compare with sibling services: if one write path checks it and another doesn't, the gap is an Error.
- Tokens for deleted users: if the token filter trusts the signature alone, a deleted account keeps working until expiry (Warning).

## What a delete removes
Follow every DELETE (and every service method that removes entities) through the JPA mappings and the DDL. `cascade = CascadeType.ALL` or `REMOVE` on a `@ManyToOne` or `@ManyToMany` removes the *shared* side — a pet type, a category, a specialty — that other records still reference:
- with `ON DELETE CASCADE` on those foreign keys (common in `schema.sql`), the database then deletes every other record that used it: deleting one owner removes other owners' pets. Silent cross-user data loss → Error.
- without it, the flush fails with a constraint violation, so records sharing that row can't be deleted at all (500, or whatever the advice maps `DataIntegrityViolationException` to) → Error.
Cascade removal belongs on compositions: `@OneToMany(mappedBy = …, cascade = ALL, orphanRemoval = true)` from an owner to its own pets is correct. Name the schema file and the mapping in the finding; the effect depends on both.

## Same rule on every path

When several endpoints do the same kind of thing (add a player to a squad, move money, change a status), check they all enforce the same business rules (caps, funds, state checks). A rule enforced on four paths and missing on the fifth is a Warning; name the paths that do enforce it.

## Security annotations (consistency only)

This skill isn't a security audit, but inconsistencies in the API layer are cheap to spot:
- If most handlers carry `@PreAuthorize`/`@Secured`/`@RolesAllowed`, flag write endpoints in the same controller that don't (Warning: "verify this is intended"). Check `SecurityFilterChain` URL rules before claiming an endpoint is open.
- `@CrossOrigin("*")` or `@CrossOrigin` with no origins on controllers — Warning; CORS belongs in central config.
- Ids from the path used to load resources owned by other users with no ownership check — mention as "verify authorization" when obvious, without claiming a vulnerability you can't confirm.

## Tests (mention, don't audit)

If the project has `@WebMvcTest`/MockMvc tests, note endpoints in scope with none, especially ones with findings — a test is the natural place to lock in a fix. Don't review test quality.
