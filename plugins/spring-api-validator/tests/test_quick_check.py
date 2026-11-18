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


if __name__ == "__main__":
    unittest.main()
