# spring-api-validator

Reviews the REST API of a Spring Boot application (Java or Kotlin, Spring MVC or WebFlux) and reports what is actually broken, with `file:line`, the runtime consequence, a fix and a confidence level for each finding. It reads what each endpoint *does* — tracing handlers into services and repositories — and compares that with what the API *claims*: HTTP verbs and statuses, parameter binding, Bean Validation, request/response DTOs and Jackson, error handling, resource ownership, database column limits and, when the project publishes one, its OpenAPI/Swagger contract. It is version-aware (Spring Boot 2.x to 4.x) and follows the team's own rules from an optional `.api-validator.md`.

## Install

Install it from the Claude plugin directory, or from its own `spring-tools` marketplace as described in the repository README.

## Use

- Ask in plain words in a Spring project: "validate the REST API in this project", "check my endpoints' HTTP methods and status codes", "review the new ProductController before I open the PR". The `spring-api-validator` skill loads on its own.
- `/spring-api-validator:validate-api [scope] [--diff [base]] [--errors-only] [--out file] [--comment owner/repo/pull/N]` — review the whole API, one controller or endpoint, or only what a branch changes; optionally post the findings on a pull request.

The plugin is instructions and reference files only. The project's repository also offers a standalone, AI-free checker and a GitHub Action for CI: https://github.com/filipelinemburger/spring-boot-api-validator

## What it runs, reads and sends

- **The review** reads the project's code, build files, configuration, migrations and OpenAPI specs through Claude Code's normal tools, and may run read-only `git` commands (`diff`, `merge-base`, `ls-files`, `blame`) to find what a branch changed. It writes a report file only when you ask for one (`--out`), and changes code only if you ask it to apply fixes.
- **Optional runtime check**: only when you ask for it (or approve it for a finding that needs it), it may start the application locally and send HTTP requests to that local or test instance — never to other hosts, and write requests only against local data.
- **Pull-request comments**: only with `--comment`, the `validate-api` command posts review comments and a summary on that pull request through GitHub (the GitHub inline-comment tool and/or the `gh` CLI, with your existing GitHub credentials). Nothing else is sent anywhere.
- **No bundled programs**, no telemetry, no data collection, no credentials or tokens read or stored by the plugin.

## License

MIT — see [LICENSE](LICENSE).
