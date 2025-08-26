# apps/imports/api/api_client_base.py
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

