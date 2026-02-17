"""Tests for input validation."""

import unittest

from business_central.validation import validate_invoice_request


class TestValidateInvoiceRequest(unittest.TestCase):
    """Test cases for validate_invoice_request."""

    # -- operation validation --

    def test_invalid_type(self):
        errors = validate_invoice_request("not a dict")
        self.assertEqual(errors, ["Request must be a JSON object."])

    def test_missing_operation(self):
        errors = validate_invoice_request({})
        self.assertTrue(any("Invalid operation" in e for e in errors))

    def test_invalid_operation(self):
        errors = validate_invoice_request({"operation": "fly"})
        self.assertTrue(any("Invalid operation" in e for e in errors))

    # -- create validation --

    def test_create_valid(self):
        req = {
            "operation": "create",
            "data": {"customerNumber": "10000"},
        }
        self.assertEqual(validate_invoice_request(req), [])

    def test_create_missing_data(self):
        req = {"operation": "create"}
        errors = validate_invoice_request(req)
        self.assertTrue(any("'data' object is required" in e for e in errors))

    def test_create_missing_required_field(self):
        req = {"operation": "create", "data": {"invoiceDate": "2025-01-01"}}
        errors = validate_invoice_request(req)
        self.assertTrue(any("customerNumber" in e for e in errors))

    def test_create_unknown_field(self):
        req = {
            "operation": "create",
            "data": {"customerNumber": "10000", "madeUpField": "x"},
        }
        errors = validate_invoice_request(req)
        self.assertTrue(any("Unknown invoice fields" in e for e in errors))

    # -- update validation --

    def test_update_valid(self):
        req = {
            "operation": "update",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
            "data": {"invoiceDate": "2025-06-01"},
        }
        self.assertEqual(validate_invoice_request(req), [])

    def test_update_missing_invoice_id(self):
        req = {"operation": "update", "data": {"invoiceDate": "2025-01-01"}}
        errors = validate_invoice_request(req)
        self.assertTrue(any("'invoice_id' is required" in e for e in errors))

    def test_update_invalid_uuid(self):
        req = {
            "operation": "update",
            "invoice_id": "not-a-uuid",
            "data": {"invoiceDate": "2025-01-01"},
        }
        errors = validate_invoice_request(req)
        self.assertTrue(any("valid UUID" in e for e in errors))

    # -- delete validation --

    def test_delete_valid(self):
        req = {
            "operation": "delete",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
        }
        self.assertEqual(validate_invoice_request(req), [])

    def test_delete_missing_invoice_id(self):
        req = {"operation": "delete"}
        errors = validate_invoice_request(req)
        self.assertTrue(any("'invoice_id' is required" in e for e in errors))

    # -- post validation --

    def test_post_valid(self):
        req = {
            "operation": "post",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
        }
        self.assertEqual(validate_invoice_request(req), [])

    def test_post_missing_invoice_id(self):
        req = {"operation": "post"}
        errors = validate_invoice_request(req)
        self.assertTrue(any("'invoice_id' is required" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
