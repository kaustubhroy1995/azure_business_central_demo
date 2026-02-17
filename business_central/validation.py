"""Input validation for Business Central invoice operations."""

from typing import List
import uuid

# Fields accepted when creating or updating an invoice.
# See: https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/api/dynamics_salesinvoice_create
ALLOWED_INVOICE_FIELDS = {
    "id",
    "number",
    "externalDocumentNumber",
    "invoiceDate",
    "postingDate",
    "dueDate",
    "customerPurchaseOrderReference",
    "customerId",
    "customerNumber",
    "customerName",
    "billToName",
    "billToCustomerId",
    "billToCustomerNumber",
    "shipToName",
    "shipToContact",
    "shipToAddressLine1",
    "shipToAddressLine2",
    "shipToCity",
    "shipToCountry",
    "shipToState",
    "shipToPostCode",
    "currencyId",
    "currencyCode",
    "email",
    "phoneNumber",
    "salesperson",
    "pricesIncludeTax",
    "remainingAmount",
    "discountAmount",
    "discountAppliedBeforeTax",
    "totalAmountExcludingTax",
    "totalTaxAmount",
    "totalAmountIncludingTax",
    "status",
    "lastModifiedDateTime",
    "salesInvoiceLines",
}

# Fields required when creating a new invoice.
REQUIRED_CREATE_FIELDS = {"customerNumber"}

# Valid operations supported by the system.
VALID_OPERATIONS = {"create", "update", "delete", "post"}


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


def validate_invoice_request(request: dict) -> List[str]:
    """Validate an incoming invoice operation request.

    Expected request format:
        {
            "operation": "create" | "update" | "delete" | "post",
            "invoice_id": "<uuid>",          # required for update/delete/post
            "data": { ... invoice fields ... } # required for create/update
        }

    Args:
        request: The JSON-parsed request dict.

    Returns:
        A list of validation error strings. Empty list means valid.
    """
    errors: List[str] = []

    if not isinstance(request, dict):
        return ["Request must be a JSON object."]

    operation = request.get("operation")
    if operation not in VALID_OPERATIONS:
        errors.append(
            f"Invalid operation '{operation}'. Must be one of: {', '.join(sorted(VALID_OPERATIONS))}."
        )
        return errors  # Can't validate further without a valid operation.

    invoice_id = request.get("invoice_id")
    data = request.get("data")

    # Operations that require an existing invoice id.
    if operation in ("update", "delete", "post"):
        if not invoice_id:
            errors.append(f"'invoice_id' is required for '{operation}' operation.")
        elif not _is_valid_uuid(invoice_id):
            errors.append(f"'invoice_id' must be a valid UUID, got '{invoice_id}'.")

    # Operations that require a body payload.
    if operation in ("create", "update"):
        if not data or not isinstance(data, dict):
            errors.append(f"'data' object is required for '{operation}' operation.")
        else:
            unknown = set(data.keys()) - ALLOWED_INVOICE_FIELDS
            if unknown:
                errors.append(
                    f"Unknown invoice fields: {', '.join(sorted(unknown))}."
                )

            if operation == "create":
                missing = REQUIRED_CREATE_FIELDS - set(data.keys())
                if missing:
                    errors.append(
                        f"Missing required fields for create: {', '.join(sorted(missing))}."
                    )

    return errors
