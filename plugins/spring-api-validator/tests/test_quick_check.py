"""Regression test for scripts/quick_check.py against the eval apps.

Run from the repository root:  python3 -m unittest discover plugins/spring-api-validator/tests
It checks that every planted mechanical defect is still detected (recall) and that the clean
parts of the apps stay quiet (precision), so rule changes can't silently break detection.
"""
import collections
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PLUGIN, "skills", "spring-api-validator", "scripts"))

import quick_check  # noqa: E402


def check(case):
    _, findings = quick_check.run_checks(os.path.join(PLUGIN, "evals", case, "files"))
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

    def test_skip_and_only(self):
        root = os.path.join(PLUGIN, "evals", "full-audit-order-service", "files")
        _, only = quick_check.run_checks(root, only={"QC10"})
        self.assertEqual(set(rules(only)), {"QC10"})
        _, skipped = quick_check.run_checks(root, skip={"QC16"})
        self.assertNotIn("QC16", rules(skipped))


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
        script = os.path.join(PLUGIN, "skills", "spring-api-validator", "scripts", "quick_check.py")
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(os.path.join(PLUGIN, "evals", "full-audit-order-service", "files"), tmp, dirs_exist_ok=True)
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
