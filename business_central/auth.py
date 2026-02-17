"""OAuth2 authentication for Business Central using Microsoft Entra ID (Azure AD)."""

import msal

# The scope required for Business Central API access.
BC_SCOPE = ["https://api.businesscentral.dynamics.com/.default"]


class Authenticator:
    """Handles OAuth2 client-credentials authentication via MSAL."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self._authority = f"https://login.microsoftonline.com/{tenant_id}"
        self._client_id = client_id
        self._client_secret = client_secret
        self._app = msal.ConfidentialClientApplication(
            client_id=self._client_id,
            client_credential=self._client_secret,
            authority=self._authority,
        )
        self._token_cache: dict | None = None

    def get_access_token(self) -> str:
        """Acquire an access token (cached if still valid).

        Returns:
            A bearer access token string.

        Raises:
            RuntimeError: If token acquisition fails.
        """
        # Try silent acquisition first (uses MSAL's internal cache).
        result = self._app.acquire_token_silent(scopes=BC_SCOPE, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=BC_SCOPE)

        if "access_token" in result:
            return result["access_token"]

        error = result.get("error_description", result.get("error", "Unknown error"))
        raise RuntimeError(f"Failed to acquire access token: {error}")
