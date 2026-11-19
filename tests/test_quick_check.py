"""Regression test for checker/quick_check.py against the eval apps.

Run from the repository root:  python3 -m unittest discover tests
It checks that every planted mechanical defect is still detected (recall) and that the clean
parts of the apps stay quiet (precision), so rule changes can't silently break detection.
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHECKER = os.path.join(ROOT, "checker")
EVALS = os.path.join(ROOT, "evals")
sys.path.insert(0, CHECKER)

import quick_check  # noqa: E402


def check(case):
    _, findings = quick_check.run_checks(os.path.join(EVALS, case, "files"))
    return findings


def rules(findings, severity=None):
    return collections.Counter(f["rule"] for f in findings if severity in (None, f["severity"]))


def at(findings, rule, filename):
    return [f for f in findings if f["rule"] == rule and f["file"].endswith(filename)]


class QuickCheckTest(unittest.TestCase):
    def test_order_service_planted_errors(self):
        f = check("full-audit-order-service")
        errors = rules(f, "error")
        for rule in ("QC03", "QC04", "QC05", "QC08", "QC09", "QC10", "QC15"):
            self.assertIn(rule, errors, rule)
        self.assertTrue(at(f, "QC10", "OrderController.java")[0]["message"].startswith("@PathVariable 'id'"))
        self.assertTrue(at(f, "QC05", "CreateOrderRequest.java"))
        self.assertTrue(at(f, "QC06", "OrderItemRequest.java"))
        self.assertTrue(at(f, "QC13", "OrderController.java"))  # GET .../cancel
        # the correct refund and status endpoints raise nothing about validation
        self.assertFalse([x for x in f if x["rule"] == "QC03" and "refund" in (x["endpoint"] or "")])

    def test_boot2_jakarta_namespace(self):
        f = check("project-rules-boot2-catalog")
        self.assertEqual([x["file"].split("/")[-1] for x in f if x["rule"] == "QC02"], ["ProductRequest.java"])
        self.assertNotIn("QC03", rules(f))  # @Valid is present; the problem is the namespace

    def test_verbs_service(self):
        f = check("http-verbs-user-service")
        self.assertEqual(rules(f, "error"), collections.Counter({"QC03": 1}))  # PATCH body without @Valid
        self.assertIn("QC12", rules(f))  # DELETE with @RequestBody
        self.assertTrue([x for x in f if x["rule"] == "QC13" and "/delete" in x["endpoint"]])

    def test_boot4_error_dispatch_and_bcrypt(self):
        f = check("boot4-jwt-error-dispatch")
        self.assertIn("QC18", rules(f, "error"))
        self.assertEqual([x["file"].split("/")[-1] for x in f if x["rule"] == "QC17"], ["RegisterRequest.java"])
        self.assertTrue(at(f, "QC16", "NoteService.java"))
        self.assertNotIn("QC02", rules(f))  # Boot 4 + jakarta is correct

    def test_loan_primitives(self):
        f = check("double-accept-transfers")
        self.assertEqual(len(at(f, "QC07", "LoanRequest.java")), 2)
        self.assertNotIn("QC13", rules(f))  # 'transfer-offers' is a resource name, not an action
        self.assertEqual(rules(f, "error"), collections.Counter())

    def test_clean_app_is_quiet(self):
        # The ownership bugs in this app are semantic; there is nothing mechanical to flag.
        self.assertEqual(check("managed-club-ownership"), [])
        # Same for method security: self-invocation and unscoped lookups need the review.
        self.assertEqual(check("clinic-method-security"), [])

    def test_warehouse_leftover_javax_and_pattern_bound(self):
        f = check("warehouse-readonly-traps")
        self.assertEqual([x["file"].split("/")[-1] for x in f if x["rule"] == "QC02"], ["StockReceiptRequest.java"])
        # currency is @Pattern("[A-Z]{3}") into VARCHAR(3): the pattern bounds the length
        self.assertNotIn("QC20", rules(f))

    def test_spring5_webflux_dates_and_functional_routes(self):
        f = check("webflux-boot27-catalog")
        self.assertEqual(len(at(f, "QC14", "ProductController.java")), 2)
        self.assertTrue(all(x["severity"] == "warning" for x in at(f, "QC14", "ProductController.java")))
        self.assertTrue(at(f, "QC24", "CategoryHandler.java"))

    def test_pattern_max_length(self):
        m = quick_check.pattern_max_length
        self.assertEqual(m("[A-Z]{3}"), 3)
        self.assertEqual(m(r"\d{4,6}"), 6)
        self.assertEqual(m("(EUR|USD|GBPX)"), 4)
        self.assertEqual(m("^[a-z]{2}-[A-Z]{2}$"), 5)
        self.assertEqual(m("(?:ab|cde)?x"), 4)
        for unbounded in ("[A-Z]+", ".*", "[a-z]{3,}", "a(b"):
            self.assertIsNone(m(unbounded), unbounded)

    def test_skip_and_only(self):
        root = os.path.join(EVALS, "full-audit-order-service", "files")
        _, only = quick_check.run_checks(root, only={"QC10"})
        self.assertEqual(set(rules(only)), {"QC10"})
        _, skipped = quick_check.run_checks(root, skip={"QC16"})
        self.assertNotIn("QC16", rules(skipped))


class KotlinAndWebFluxTest(unittest.TestCase):
    def test_kotlin_books(self):
        f = check("kotlin-books-api")
        self.assertEqual(rules(f, "error"), collections.Counter({"QC19": 2, "QC03": 1, "QC08": 1, "QC10": 1}))
        qc19 = sorted(x["message"].split("property ")[1].split(" ")[0] for x in f if x["rule"] == "QC19")
        self.assertEqual(qc19, ["CreateBookRequest.isbn", "CreateBookRequest.title"])  # not the @field: ones
        self.assertIn("Int?", at(f, "QC08", "BookController.kt")[0]["fix"])
        self.assertIn("NullPointerException", at(f, "QC16", "BookService.kt")[0]["message"])
        self.assertTrue([x for x in f if x["rule"] == "QC13" and "/reserve" in x["endpoint"]])

    def test_webflux_shop(self):
        f = check("webflux-shop-api")
        # No QC24: on Spring 6 (Boot 3.3) global @RestControllerAdvice also handles functional routes.
        self.assertEqual(set(rules(f)), {"QC21", "QC22", "QC23"})
        self.assertTrue(at(f, "QC21", "StockHandler.java"))       # bodyToMono without a Validator
        self.assertTrue(at(f, "QC22", "ProductController.java"))  # block() on the event loop
        self.assertIn("→ get", at(f, "QC23", "ProductController.java")[0]["endpoint"])  # not /price (switchIfEmpty)

    def test_advice_and_functional_routes_depend_on_version_and_scope(self):
        import shutil
        import tempfile
        src = os.path.join(EVALS, "webflux-shop-api", "files")
        advice = os.path.join("src", "main", "java", "com", "example", "shop", "common", "ApiExceptionHandler.java")
        for change, label in ((("pom.xml", "<version>3.3.5</version>", "<version>2.7.18</version>"), "WebFlux on Spring 5"),
                              ((advice, "@RestControllerAdvice\n",
                                '@RestControllerAdvice(basePackages = "com.example.shop.product")\n'), "scoped advice")):
            with tempfile.TemporaryDirectory() as tmp:
                shutil.copytree(src, tmp, dirs_exist_ok=True)
                path = os.path.join(tmp, change[0])
                with open(path) as fh:
                    text = fh.read()
                self.assertIn(change[1], text)
                with open(path, "w") as fh:
                    fh.write(text.replace(change[1], change[2]))
                _, f = quick_check.run_checks(tmp, only={"QC24"})
                self.assertEqual(len(f), 1, label)
                self.assertIn("NotFoundException", f[0]["message"])

    def test_functional_routes_in_inventory(self):
        import list_endpoints
        root = os.path.join(EVALS, "webflux-shop-api", "files")
        found = []
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if fn.endswith(".java"):
                    found += list_endpoints.scan_functional(os.path.join(dirpath, fn), root)
        self.assertEqual(sorted((e["method"], e["path"], e["handler"]) for e in found),
                         [("GET", "/api/stock/{sku}", "handler::get"),
                          ("POST", "/api/stock/{sku}/reservations", "handler::reserve")])


class OpenApiDriftTest(unittest.TestCase):
    def test_drifted_spec(self):
        f = check("openapi-drift-orders")
        drift = [x for x in f if x["rule"] in ("QC25", "QC26", "QC27", "QC28", "QC29")]
        by = collections.Counter((x["rule"], x["severity"]) for x in drift)
        self.assertEqual(by, collections.Counter({
            ("QC25", "error"): 1, ("QC25", "suggestion"): 1,     # missing customer-orders op; undocumented DELETE
            ("QC27", "warning"): 1,                              # 201 documented, 200 returned
            ("QC26", "warning"): 2,                              # shippingAddress, status not enforced
            ("QC28", "warning"): 2, ("QC28", "suggestion"): 1,   # orderNumber missing, itemCount type; number extra
            ("QC29", "warning"): 2}))                            # @ApiResponse 204; @Schema required unchecked
        self.assertIn("/v1/customers/{customerId}/orders", [x for x in drift if x["severity"] == "error"][0]["message"])
        # {orderId} vs {id} and the /api prefix must not produce drift for the operations that exist
        self.assertFalse([x for x in drift if x["rule"] == "QC25" and "{orderId}" in x["message"]])

    def test_yaml_reader(self):
        import openapi_spec
        doc = openapi_spec.yaml_load(
            "openapi: 3.0.3\ninfo:\n  title: A  # comment\n  description: |\n    line: one\n    has # hash\n"
            "servers:\n  - url: https://x.test/api/v2\ntags: [a, 'b c']\npaths:\n  /x/{id}:\n    get:\n"
            "      responses:\n        200: {description: ok}\n        '404':\n          description: missing\n")
        self.assertEqual(doc["info"]["title"], "A")
        self.assertEqual(doc["info"]["description"], "line: one\nhas # hash")
        self.assertEqual(doc["tags"], ["a", "b c"])
        self.assertEqual(sorted(map(str, doc["paths"]["/x/{id}"]["get"]["responses"])), ["200", "404"])
        spec = openapi_spec.Spec("x.yaml", ".", doc)
        self.assertEqual(spec.base_path, "/api/v2")
        self.assertEqual(spec.success_codes(doc["paths"]["/x/{id}"]["get"]), [200])


class SchemaLimitsTest(unittest.TestCase):
    """QC20: request limits vs. database columns."""

    def test_wage_copied_into_narrower_column(self):
        f = [x for x in check("double-accept-transfers") if x["rule"] == "QC20"]
        wage = [x for x in f if "MakeOfferRequest.wage" in x["message"]]
        self.assertEqual(len(wage), 1)
        self.assertIn("players.wage NUMERIC(10,2)", wage[0]["message"])  # the narrower of the two wage columns
        self.assertEqual(wage[0]["confidence"], "verify")

    def test_matching_limits_and_lookups_stay_quiet(self):
        # notes: @Size limits equal the VARCHAR columns; LoginRequest only looks values up
        self.assertEqual([x for x in check("boot4-jwt-error-dispatch") if x["rule"] == "QC20"], [])

    def test_migration_history_and_liquibase(self):
        schema = {}
        quick_check.parse_sql_schema(
            "CREATE TABLE IF NOT EXISTS public.users (\n  id UUID PRIMARY KEY,\n  name VARCHAR(50) NOT NULL,\n"
            "  CONSTRAINT uq UNIQUE (name)\n);\n"
            "ALTER TABLE users ADD COLUMN nick varchar(20), ADD COLUMN bio TEXT;\n"
            "ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(80);\n"
            "ALTER TABLE users RENAME COLUMN nick TO handle;\n"
            "-- ALTER TABLE users ADD COLUMN ignored VARCHAR(1);\n"
            "ALTER TABLE accounts ADD balance NUMERIC(12, 2);\n", "V1__x.sql", schema)
        quick_check.parse_liquibase_xml(
            '<changeSet id="1"><createTable tableName="orders"><column name="code" type="varchar(12)"/>'
            '<column name="total" type="DECIMAL(10,2)"/></createTable>'
            '<modifyDataType tableName="orders" columnName="code" newDataType="varchar(16)"/></changeSet>',
            "changelog.xml", schema)
        limits = {k: v[0] for k, v in schema.items()}
        self.assertEqual(limits[("users", "name")], ("varchar", 80))       # ALTER … TYPE wins over CREATE
        self.assertEqual(limits[("users", "handle")], ("varchar", 20))     # renamed column keeps its limit
        self.assertNotIn(("users", "nick"), limits)
        self.assertNotIn(("users", "ignored"), limits)                     # commented out
        self.assertNotIn(("users", "bio"), limits)                         # TEXT has no limit
        self.assertEqual(limits[("accounts", "balance")], ("numeric", 12, 2))
        self.assertEqual(limits[("orders", "code")], ("varchar", 16))
        self.assertEqual(limits[("orders", "total")], ("numeric", 10, 2))


class DiffScopeTest(unittest.TestCase):
    """--diff-base reports only findings in files the branch changed."""

    def test_only_changed_files_are_reported(self):
        import shutil
        import subprocess
        import tempfile
        script = os.path.join(CHECKER, "quick_check.py")
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(os.path.join(EVALS, "full-audit-order-service", "files"), tmp, dirs_exist_ok=True)
            git = ["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@example.com"]
            subprocess.run(git + ["init", "-q", "-b", "main"], check=True)
            subprocess.run(git + ["add", "-A"], check=True)
            subprocess.run(git + ["commit", "-qm", "base"], check=True)
            subprocess.run(git + ["checkout", "-qb", "feature"], check=True)
            new = os.path.join(tmp, "src/main/java/com/acme/orders/dto/NoteRequest.java")
            with open(new, "w") as fh:
                fh.write("package com.acme.orders.dto;\n\nimport jakarta.validation.constraints.NotBlank;\n\n"
                         "public record NoteRequest(@NotBlank Long orderId) {}\n")
            out = subprocess.run([sys.executable, script, tmp, "--diff-base", "main", "--format", "json"],
                                 capture_output=True, text=True, check=True)
            import json
            findings = json.loads(out.stdout)["findings"]
            self.assertEqual([(f["rule"], os.path.basename(f["file"])) for f in findings],
                             [("QC05", "NoteRequest.java")])
            bad = subprocess.run([sys.executable, script, tmp, "--diff-base", "no-such-ref"], capture_output=True)
            self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
