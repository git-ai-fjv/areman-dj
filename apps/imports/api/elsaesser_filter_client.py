# apps/imports/api/elsaesser_filter_client.py
from __future__ import annotations
import uuid
import logging
from typing import Any, Dict, List

from apps.imports.api.api_client_base import BaseApiClient, ApiError


class FilterTechnikApiClient(BaseApiClient):
    """Client for Filter-Technik Store API (Shopware 6.6)."""

    def __init__(self, base_url: str, access_key: str, username: str, password: str) -> None:
        super().__init__(base_url, access_key)
        self.username = username
        self.password = password
        # Context token required for all requests
        self.context_token = str(uuid.uuid4()).replace("-", "")
        self.log = logging.getLogger(self.__class__.__name__)

    def login(self) -> None:
        """Authenticate and refresh context token."""
        path = "account/login"
        payload = {"username": self.username, "password": self.password}
        resp = self._post(path, payload, context_token=self.context_token)

        token = resp.headers.get("sw-context-token")
        if not token:
            raise ApiError("Login failed: context token missing in response headers")
        self.context_token = token
        self.log.info("Login successful, context token: %s", self.context_token)

    def get_product_by_manufacturer_number(self, number: str) -> List[Dict[str, Any]]:
        """Fetch products by manufacturerNumber."""
        path = "product"
        payload = {
            "page": "1",
            "filter": [{"type": "equals", "field": "manufacturerNumber", "value": number}],
        }
        resp = self._post(path, payload, context_token=self.context_token)
        return resp.json().get("elements", [])

    def get_product_by_sku(self, sku: str) -> List[Dict[str, Any]]:
        """Fetch products by productNumber (SKU)."""
        path = "product"
        payload = {
            "page": "1",
            "filter": [{"type": "equals", "field": "productNumber", "value": sku}],
        }
        resp = self._post(path, payload, context_token=self.context_token)
        return resp.json().get("elements", [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    BASE_URL = "https://www.filter-technik.de/store-api"
    API_KEY = "SWSCQU9ZETYXSGPTB2DSAFM2WQ"
    USERNAME = "bestellung@areman.de"
    PASSWORD = "1c6a4c1b"

    client = FilterTechnikApiClient(
        base_url=BASE_URL,
        access_key=API_KEY,
        username=USERNAME,
        password=PASSWORD,
    )

    try:
        client.login()
        products = client.get_product_by_manufacturer_number("W 930/13")
        print("Fetched products:", products)
    except Exception as e:
        print("❌ Error during API test:", e)


