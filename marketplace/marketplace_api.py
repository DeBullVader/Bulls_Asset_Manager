"""
marketplace_api.py
──────────────────
Thin HTTP client for the PolyAssetVault addon API.
All network calls go through here so error handling is centralised.

Usage:
    from .marketplace_api import MarketplaceAPI
    api = MarketplaceAPI(base_url, device_token)
    ok, data = api.get("/addon/auth/me")
"""

import json
import urllib.request
import urllib.error
import urllib.parse

from ..utils.addon_logger import addon_logger


class MarketplaceAPI:
    def __init__(self, base_url: str, device_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.device_token = device_token

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _headers(self, extra: dict = None) -> dict:
        h = {"Content-Type": "application/json"}
        if self.device_token:
            h["X-Addon-Token"] = self.device_token
        if extra:
            h.update(extra)
        return h

    def _request(self, method: str, endpoint: str, data: dict = None,
                 bearer_token: str = None) -> tuple[bool, dict]:
        """
        Make an HTTP request. Returns (success, response_dict).
        On network/parse error returns (False, {"message": "..."}).
        """
        url = self.base_url + endpoint
        body = json.dumps(data).encode() if data else None

        extra = {}
        if bearer_token:
            extra["Authorization"] = f"Bearer {bearer_token}"

        req = urllib.request.Request(
            url,
            data=body,
            headers=self._headers(extra),
            method=method,
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode()
                return True, json.loads(raw) if raw else {}

        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode())
            except Exception:
                error_body = {"message": f"HTTP {e.code}: {e.reason}"}
            addon_logger.warning(f"API {method} {endpoint} → {e.code}: {error_body}")
            return False, error_body

        except urllib.error.URLError as e:
            msg = f"Network error reaching {url}: {e.reason}"
            addon_logger.error(msg)
            return False, {"message": msg}

        except Exception as e:
            addon_logger.exception(f"Unexpected error in API call {method} {endpoint}")
            return False, {"message": str(e)}

    # ── Public methods ────────────────────────────────────────────────────────

    def get(self, endpoint: str) -> tuple[bool, dict]:
        return self._request("GET", endpoint)

    def post(self, endpoint: str, data: dict = None,
             bearer_token: str = None) -> tuple[bool, dict]:
        return self._request("POST", endpoint, data=data, bearer_token=bearer_token)

    def delete(self, endpoint: str) -> tuple[bool, dict]:
        return self._request("DELETE", endpoint)

    # ── Auth convenience methods ──────────────────────────────────────────────

    def exchange_jwt_for_device_token(self, jwt: str, meta: dict) -> tuple[bool, dict]:
        """POST /api/addon/auth/device-token using a short-lived JWT."""
        return self._request(
            "POST", "/api/addon/auth/device-token",
            data=meta,
            bearer_token=jwt,
        )

    def verify_token(self) -> tuple[bool, dict]:
        """GET /api/addon/auth/me — check stored device token is still valid."""
        return self.get("/api/addon/auth/me")

    def revoke_token(self) -> tuple[bool, dict]:
        """DELETE /api/addon/auth/device-token — logout."""
        return self.delete("/api/addon/auth/device-token")

    # ── Data methods ──────────────────────────────────────────────────────────

    def get_purchases(self) -> tuple[bool, dict]:
        return self.get("/api/addon/purchases")

    def browse_products(self, search: str = "", category: str = "",
                        page: int = 1, limit: int = 20) -> tuple[bool, dict]:
        params = urllib.parse.urlencode({
            k: v for k, v in {
                "search": search,
                "category": category,
                "page": page,
                "limit": limit,
            }.items() if v
        })
        endpoint = f"/api/addon/products?{params}" if params else "/api/addon/products"
        return self.get(endpoint)

    def get_product(self, product_id: str) -> tuple[bool, dict]:
        return self.get(f"/api/addon/products/{product_id}")

    def download_product(self, product_id: str, dest_path: str,
                         progress_callback=None) -> tuple[bool, str]:
        """
        Stream GET /api/addon/products/:id/download directly to dest_path on disk.

        Returns (True, "") on success, (False, error_message) on failure.
        progress_callback(bytes_received, total_bytes) is called during download
        if provided; total_bytes may be None if the server omits Content-Length.

        Handles:
          - 503: download not yet available (returns False with message)
          - 403: not owner (returns False with message)
          - Binary stream: written in 64KB chunks to avoid memory pressure
        """
        import os
        url = self.base_url + f"/api/addon/products/{product_id}/download"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = resp.headers.get("Content-Length")
                total_bytes = int(total) if total else None
                received = 0
                chunk_size = 65536  # 64 KB

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        received += len(chunk)
                        if progress_callback:
                            progress_callback(received, total_bytes)

            addon_logger.info(f"Downloaded product {product_id} to {dest_path}")
            return True, ""

        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode())
            except Exception:
                error_body = {"message": f"HTTP {e.code}: {e.reason}"}
            msg = error_body.get("message", f"HTTP {e.code}")
            addon_logger.warning(f"Download failed for {product_id}: {msg}")
            return False, msg

        except urllib.error.URLError as e:
            msg = f"Network error: {e.reason}"
            addon_logger.error(msg)
            return False, msg

        except Exception as e:
            addon_logger.exception(f"Unexpected error downloading {product_id}")
            return False, str(e)
