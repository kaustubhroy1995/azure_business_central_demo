"""Tests for the Business Central client (with mocked HTTP)."""

import json
import unittest
from unittest.mock import MagicMock, patch

from business_central.client import BusinessCentralClient


def _make_config():
    return {
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "environment": "sandbox",
        "company_id": "test-company-id",
    }


class TestBusinessCentralClient(unittest.TestCase):
    """Test BusinessCentralClient.process_request with mocked auth + HTTP."""

    def setUp(self):
        patcher = patch("business_central.client.Authenticator")
        self.mock_auth_cls = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_auth_cls.return_value.get_access_token.return_value = "fake-token"

    def _make_client(self):
        return BusinessCentralClient(_make_config())

    # -- validation errors --

    def test_validation_error_returns_failure(self):
        client = self._make_client()
        result = client.process_request({"operation": "create"})
        self.assertFalse(result["success"])
        self.assertTrue(len(result["errors"]) > 0)

    # -- create --

    @patch("business_central.client.requests.post")
    def test_create_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "new-id", "number": "INV001"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        client = self._make_client()
        result = client.process_request({
            "operation": "create",
            "data": {"customerNumber": "10000"},
        })
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["id"], "new-id")
        mock_post.assert_called_once()

    # -- update --

    @patch("business_central.client.requests.patch")
    def test_update_success(self, mock_patch):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "inv-id", "invoiceDate": "2025-06-01"}
        mock_resp.raise_for_status.return_value = None
        mock_patch.return_value = mock_resp

        client = self._make_client()
        result = client.process_request({
            "operation": "update",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
            "data": {"invoiceDate": "2025-06-01"},
        })
        self.assertTrue(result["success"])
        mock_patch.assert_called_once()

    # -- delete --

    @patch("business_central.client.requests.delete")
    def test_delete_success(self, mock_delete):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_delete.return_value = mock_resp

        client = self._make_client()
        result = client.process_request({
            "operation": "delete",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
        })
        self.assertTrue(result["success"])
        self.assertIsNone(result["data"])
        mock_delete.assert_called_once()

    # -- post --

    @patch("business_central.client.requests.post")
    def test_post_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.content = b"{}"
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        client = self._make_client()
        result = client.process_request({
            "operation": "post",
            "invoice_id": "00000000-0000-0000-0000-000000000001",
        })
        self.assertTrue(result["success"])

    # -- HTTP error handling --

    @patch("business_central.client.requests.post")
    def test_http_error_is_caught(self, mock_post):
        import requests
        mock_resp = MagicMock()
        mock_resp.text = "Internal Server Error"
        http_err = requests.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_err
        mock_post.return_value = mock_resp

        client = self._make_client()
        result = client.process_request({
            "operation": "create",
            "data": {"customerNumber": "10000"},
        })
        self.assertFalse(result["success"])
        self.assertTrue(len(result["errors"]) > 0)


class TestConfigLoading(unittest.TestCase):
    """Test config loading."""

    def test_missing_file(self):
        from business_central.config import load_config
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path.json")

    def test_missing_keys(self):
        import tempfile
        from business_central.config import load_config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"tenant_id": "x"}, f)
            f.flush()
            with self.assertRaises(ValueError):
                load_config(f.name)


if __name__ == "__main__":
    unittest.main()
