# Business Central Invoice Management System

A Python system for managing sales invoices in Microsoft Dynamics 365 Business Central. It accepts JSON input and creates, updates, deletes, or posts invoices via the Business Central API v2.0.

## Features

- **CRUD + Post operations** on sales invoices via the Business Central API
- **Input validation** — verifies JSON payloads before sending requests
- **Concurrency control** — limits to 5 simultaneous in-flight requests
- **Rate limiting** — enforces a maximum of 50 requests per minute
- **OAuth2 authentication** via Microsoft Entra ID (Azure AD) client credentials flow

## Prerequisites

### What to Ask Your Admin

To use this system, you need an Azure AD **app registration** with access to Business Central. Ask your Microsoft 365 / Azure administrator for:

| Item | Description | Where to Find It |
|---|---|---|
| **Tenant ID** | Your Azure AD (Entra ID) tenant identifier | Azure Portal → Azure Active Directory → Overview |
| **Client ID** | The Application (client) ID of the app registration | Azure Portal → App registrations → *your app* → Overview |
| **Client Secret** | A secret generated for the app registration | Azure Portal → App registrations → *your app* → Certificates & secrets |
| **Environment** | Business Central environment name (e.g. `production`, `sandbox`) | Business Central Admin Center → Environments |
| **Company ID** | GUID of the target company in Business Central | Business Central → Settings → Company Information, or via the API |

### App Registration Setup (Admin Steps)

1. Go to **Azure Portal → App registrations → New registration**.
2. Under **API permissions**, add:
   - **Dynamics 365 Business Central → Application permissions:**
     - `API.ReadWrite.All`
3. Click **Grant admin consent**.
4. Under **Certificates & secrets**, create a new **Client secret** and record the value.
5. Share the Tenant ID, Client ID, Client Secret, Environment name, and Company ID with the developer.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example config file:
   ```bash
   cp config.example.json config.json
   ```
2. Fill in your credentials in `config.json`. The file is git-ignored and will not be committed.

See [`config.example.json`](config.example.json) for detailed documentation of each field.

## Usage

```python
from business_central.config import load_config
from business_central.client import BusinessCentralClient

config = load_config()  # loads config.json
client = BusinessCentralClient(config)

# Create an invoice
result = client.process_request({
    "operation": "create",
    "data": {
        "customerNumber": "10000",
        "invoiceDate": "2025-06-01"
    }
})
print(result)
# {"success": True, "data": {"id": "...", "number": "INV001", ...}, "errors": []}

# Update an invoice
result = client.process_request({
    "operation": "update",
    "invoice_id": "00000000-0000-0000-0000-000000000001",
    "data": {"invoiceDate": "2025-07-01"}
})

# Post (finalize) an invoice
result = client.process_request({
    "operation": "post",
    "invoice_id": "00000000-0000-0000-0000-000000000001"
})

# Delete an invoice
result = client.process_request({
    "operation": "delete",
    "invoice_id": "00000000-0000-0000-0000-000000000001"
})
```

## Request Format

Every request is a JSON object with the following structure:

| Field | Type | Required | Description |
|---|---|---|---|
| `operation` | string | Yes | One of `create`, `update`, `delete`, `post` |
| `invoice_id` | string (UUID) | For update/delete/post | The ID of the existing invoice |
| `data` | object | For create/update | Invoice fields (see below) |
| `etag` | string | Optional (update) | ETag for optimistic concurrency control |

### Invoice Data Fields

Fields correspond to the [Business Central Sales Invoice API](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/api/dynamics_salesinvoice_create):

`customerNumber` (required for create), `customerId`, `customerName`, `invoiceDate`, `postingDate`, `dueDate`, `currencyCode`, `email`, `phoneNumber`, `salesperson`, `number`, `externalDocumentNumber`, and more. Unknown fields are rejected during validation.

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Architecture

```
business_central/
├── __init__.py
├── auth.py          # OAuth2 client-credentials authentication via MSAL
├── client.py        # High-level API client with validation and queuing
├── config.py        # Configuration file loader
├── queue.py         # Thread-safe request queue with concurrency + rate limits
└── validation.py    # JSON input validation for invoice operations
tests/
├── __init__.py
├── test_client.py   # Client tests with mocked HTTP
├── test_queue.py    # Queue concurrency and rate-limit tests
└── test_validation.py  # Input validation tests
```
