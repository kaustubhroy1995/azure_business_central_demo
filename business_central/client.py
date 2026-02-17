"""Business Central invoice API client."""

import logging
from typing import Optional

import requests

from .auth import Authenticator
from .queue import RequestQueue
from .validation import validate_invoice_request

logger = logging.getLogger(__name__)

# Business Central API v2.0 base URL template.
BASE_URL = (
    "https://api.businesscentral.dynamics.com/v2.0/"
    "{tenant_id}/{environment}/api/v2.0/companies({company_id})"
)


class BusinessCentralClient:
    """Client for Business Central Sales Invoice API operations.

    Supports create, update, delete, and post operations on sales invoices,
    with built-in concurrency and rate limiting.

    Args:
        config: Dict with keys tenant_id, client_id, client_secret,
                environment, company_id.
        max_concurrent: Max concurrent requests (default 5).
        max_per_minute: Max requests per minute (default 50).
    """

    def __init__(
        self,
        config: dict,
        max_concurrent: int = 5,
        max_per_minute: int = 50,
    ):
        self._config = config
        self._auth = Authenticator(
            tenant_id=config["tenant_id"],
            client_id=config["client_id"],
            client_secret=config["client_secret"],
        )
        self._queue = RequestQueue(
            max_concurrent=max_concurrent,
            max_per_minute=max_per_minute,
        )
        self._base_url = BASE_URL.format(
            tenant_id=config["tenant_id"],
            environment=config["environment"],
            company_id=config["company_id"],
        )

    def _headers(self) -> dict:
        """Build HTTP headers with a fresh access token."""
        token = self._auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _invoices_url(self, invoice_id: Optional[str] = None) -> str:
        """Return the invoices endpoint URL."""
        url = f"{self._base_url}/salesInvoices"
        if invoice_id:
            url += f"({invoice_id})"
        return url

    # -- low-level HTTP helpers executed inside the queue --

    def _do_create(self, data: dict) -> dict:
        url = self._invoices_url()
        logger.info("POST %s", url)
        resp = requests.post(url, headers=self._headers(), json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _do_update(self, invoice_id: str, data: dict, etag: Optional[str] = None) -> dict:
        url = self._invoices_url(invoice_id)
        headers = self._headers()
        if etag:
            headers["If-Match"] = etag
        else:
            headers["If-Match"] = "*"
        logger.info("PATCH %s", url)
        resp = requests.patch(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _do_delete(self, invoice_id: str) -> None:
        url = self._invoices_url(invoice_id)
        logger.info("DELETE %s", url)
        resp = requests.delete(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()

    def _do_post(self, invoice_id: str) -> dict:
        url = f"{self._base_url}/salesInvoices({invoice_id})/Microsoft.NAV.post"
        logger.info("POST %s", url)
        resp = requests.post(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # -- public interface --

    def process_request(self, request: dict) -> dict:
        """Validate and execute an invoice operation.

        Args:
            request: Dict with keys 'operation', optionally 'invoice_id'
                     and 'data'. See validation.py for the schema.

        Returns:
            A result dict: {"success": bool, "data": ..., "errors": [...]}.
        """
        errors = validate_invoice_request(request)
        if errors:
            return {"success": False, "data": None, "errors": errors}

        operation = request["operation"]
        invoice_id = request.get("invoice_id")
        data = request.get("data", {})
        etag = request.get("etag")

        try:
            if operation == "create":
                result = self._queue.submit(self._do_create, data)
            elif operation == "update":
                result = self._queue.submit(self._do_update, invoice_id, data, etag)
            elif operation == "delete":
                self._queue.submit(self._do_delete, invoice_id)
                result = None
            elif operation == "post":
                result = self._queue.submit(self._do_post, invoice_id)
            else:
                return {"success": False, "data": None, "errors": [f"Unsupported operation: {operation}"]}

            return {"success": True, "data": result, "errors": []}
        except requests.HTTPError as exc:
            body = ""
            if exc.response is not None:
                body = exc.response.text
            logger.error("HTTP error during %s: %s – %s", operation, exc, body)
            return {"success": False, "data": None, "errors": [str(exc), body]}
        except Exception as exc:
            logger.error("Unexpected error during %s: %s", operation, exc)
            return {"success": False, "data": None, "errors": [str(exc)]}
