# apps/imports/api/api_client_base.py
# apps/imports/api/api_client_base.py
"""
Purpose:
    Provides a reusable base client for Store-API style integrations.
    Handles session setup, request headers, and POST requests with error handling.

Context:
    Part of the `imports` app. Serves as the common foundation for external
    API connectors (e.g. Shopware, suppliers). Ensures consistent logging,
    authentication, and error reporting.

Used by:
    - Specialized API clients in `apps/imports/api/` that inherit from BaseApiClient
    - Import services that need to fetch or push data to external systems

Depends on:
    - requests (HTTP session handling)
    - logging for structured error reporting
    - apps.imports.api.api_client_base.ApiError for request failures

Example:
    from apps.imports.api.api_client_base import BaseApiClient

    client = BaseApiClient(base_url="https://shop/api", access_key="xyz123")
    response = client._post("search/product", {"filter": []})
    print(response.status_code, response.json())
"""

from __future__ import annotations
import requests
import logging
import traceback
from typing import Any, Dict, Optional


class ApiError(Exception):
    """Raised when an API request fails."""


class BaseApiClient:
    """Reusable base client for Store-API based integrations."""

    def __init__(self, base_url: str, access_key: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_key = access_key
        self.timeout = timeout
        self.session = requests.Session()
        self.log = logging.getLogger(self.__class__.__name__)

    def _headers(self, context_token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "sw-access-key": self.access_key,
        }
        if context_token:
            headers["sw-context-token"] = context_token
        return headers

    def _post(self, path: str, payload: Dict[str, Any], context_token: Optional[str] = None) -> requests.Response:
        """Execute a POST request and return the full Response object."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self.session.post(
                url, json=payload, headers=self._headers(context_token), timeout=self.timeout
            )
            if resp.status_code >= 400:
                raise ApiError(f"POST {url} failed [{resp.status_code}]: {resp.text}")
            return resp  # 🔑 Response zurückgeben, nicht .json()
        except Exception as e:
            tb = traceback.format_exc()
            self.log.error("API POST failed: %s\n%s", e, tb)
            raise

