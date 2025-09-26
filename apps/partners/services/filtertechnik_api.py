#!/usr/bin/env python3
# apps/partners/services/filtertechnik_api.py
"""
Purpose:
    Service client for interacting with the Filter-Technik (Shopware Store-API).
    Handles context token retrieval and provides helper methods to fetch product
    data, e.g. by SKU.

Context:
    Located in `apps.partners.services`. This client is used by importers and
    partner integrations to query live product data from the Filter-Technik API.

Used by:
    - Import commands (e.g., `import_elsaesser`)
    - Partner services or background jobs needing product lookups

Depends on:
    - requests (HTTP requests to the Shopware Store-API)
    - Python stdlib (uuid, traceback)

Example:
    client = FilterTechnikApiClient(
        base_url="https://www.filter-technik.de/store-api",
        access_key="SWSCQU9ZETYXSGPTB2DSAFM2WQ"
    )
    client.ensure_context()
    product = client.get_product_by_sku("12345")
    print(product)
"""


from __future__ import annotations
import requests, uuid, traceback
from typing import Any, Dict, Optional

class FilterTechnikApiClient:
    """Client for the Filter-Technik (Shopware Store-API) supplier."""

    def __init__(self, base_url: str, access_key: str, context_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.access_key = access_key
        self.context_token = context_token

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json", "sw-access-key": self.access_key}
        if self.context_token:
            headers["sw-context-token"] = self.context_token
        return headers

    def ensure_context(self) -> None:
        """Fetch context token if missing."""
        if not self.context_token:
            try:
                r = requests.get(f"{self.base_url}/context", headers=self._headers(), timeout=10)
                r.raise_for_status()
                self.context_token = r.json().get("token")
                print(f"✅ New context token acquired: {self.context_token}")
            except Exception as e:
                tb = traceback.format_exc()
                print(f"❌ Failed to fetch context token: {e}\n{tb}")
                raise

    def get_product_by_sku(self, sku: str) -> Dict[str, Any]:
        """Fetch product by SKU (productNumber)."""
        body = {"page": "1", "filter": [{"type": "equals", "field": "productNumber", "value": sku}]}
        return self._post_product(body)

    def _post_product(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            r = requests.post(f"{self.base_url}/product", json=body, headers=self._headers(), timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            tb = traceback.format_exc()
            print(f"❌ Product request failed: {e}\n{tb}")
            raise
