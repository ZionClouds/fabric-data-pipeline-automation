"""
Base Client for Microsoft Fabric SDK

Provides async HTTP client with OAuth2 authentication for all Fabric APIs.
"""

from __future__ import annotations
import httpx
import logging
import base64
import json
from typing import Dict, Any, Optional, List, TypeVar, Type
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class FabricBaseClient:
    """
    Base async client for Microsoft Fabric REST API.

    Handles authentication, request/response processing, and common operations.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        base_url: str = "https://api.fabric.microsoft.com/v1"
    ):
        """
        Initialize the Fabric API client.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Service principal client ID
            client_secret: Service principal client secret
            base_url: Fabric API base URL
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self._access_token: Optional[str] = None

    async def get_access_token(self) -> str:
        """
        Get OAuth2 access token for Fabric API.
        Token is fetched fresh each time to avoid expiration issues.

        Returns:
            Access token string
        """
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://api.fabric.microsoft.com/.default",
            "grant_type": "client_credentials"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            logger.info("Successfully obtained fresh Fabric API access token")
            return self._access_token

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers with fresh access token."""
        token = await self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> httpx.Response:
        """
        Make an HTTP request to Fabric API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (relative to base_url)
            json_data: JSON payload for POST/PUT/PATCH
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            httpx.Response object
        """
        headers = await self._get_headers()
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_data,
                params=params
            )
            return response

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ) -> httpx.Response:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params, timeout=timeout)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> httpx.Response:
        """Make a POST request."""
        return await self._request("POST", endpoint, json_data=json_data, timeout=timeout)

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> httpx.Response:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, json_data=json_data, timeout=timeout)

    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0
    ) -> httpx.Response:
        """Make a PATCH request."""
        return await self._request("PATCH", endpoint, json_data=json_data, timeout=timeout)

    async def delete(
        self,
        endpoint: str,
        timeout: float = 30.0
    ) -> httpx.Response:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint, timeout=timeout)

    def _handle_response(
        self,
        response: httpx.Response,
        success_codes: List[int] = None
    ) -> Dict[str, Any]:
        """
        Handle API response and return JSON data.

        Args:
            response: httpx.Response object
            success_codes: List of HTTP status codes considered successful

        Returns:
            Response JSON data

        Raises:
            Exception on error responses
        """
        success_codes = success_codes or [200, 201, 202]

        if response.status_code in success_codes:
            if response.text and response.text != 'null':
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {}
            return {}
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error(f"Fabric API error: {error_msg}")
            raise Exception(error_msg)

    def _parse_response(
        self,
        response: httpx.Response,
        model_class: Type[T],
        success_codes: List[int] = None
    ) -> T:
        """
        Parse API response into a Pydantic model.

        Args:
            response: httpx.Response object
            model_class: Pydantic model class to parse into
            success_codes: List of HTTP status codes considered successful

        Returns:
            Parsed Pydantic model instance
        """
        data = self._handle_response(response, success_codes)
        return model_class.model_validate(data)

    @staticmethod
    def encode_definition(content: Dict[str, Any], path: str = "content.json") -> Dict[str, Any]:
        """
        Encode content as base64 for Fabric API definition.

        Args:
            content: Dictionary content to encode
            path: Path name for the definition part

        Returns:
            Definition object with base64-encoded payload
        """
        content_json = json.dumps(content)
        content_base64 = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')

        return {
            "parts": [
                {
                    "path": path,
                    "payload": content_base64,
                    "payloadType": "InlineBase64"
                }
            ]
        }

    @staticmethod
    def decode_definition(definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode base64 definition from Fabric API.

        Args:
            definition: Definition object from API response

        Returns:
            Decoded content dictionary
        """
        if not definition or "parts" not in definition:
            return {}

        for part in definition.get("parts", []):
            if part.get("payloadType") == "InlineBase64":
                payload = part.get("payload", "")
                try:
                    decoded = base64.b64decode(payload).decode('utf-8')
                    return json.loads(decoded)
                except (ValueError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to decode definition: {e}")
                    return {}

        return {}
