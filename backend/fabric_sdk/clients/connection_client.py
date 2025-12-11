"""
Connection Client for Microsoft Fabric SDK

Provides async operations for connection management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.core import (
    CreateConnectionRequest,
    Connection,
    Connections,
    CredentialType,
    ConnectivityType,
    DataSourceType,
)

logger = logging.getLogger(__name__)


class ConnectionClient(FabricBaseClient):
    """
    Client for Connection operations in Microsoft Fabric.

    Connections are used to authenticate to external data sources.
    """

    async def list_connections(
        self,
        continuation_token: Optional[str] = None
    ) -> Connections:
        """List all connections."""
        endpoint = "/connections"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Connections)

    async def get_connection(self, connection_id: str) -> Connection:
        """Get a specific connection."""
        endpoint = f"/connections/{connection_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, Connection)

    async def create_connection(
        self,
        display_name: str,
        connectivity_type: ConnectivityType,
        data_source_type: DataSourceType,
        connection_path: str,
        credential_type: CredentialType,
        credentials: Dict[str, Any],
        privacy_level: str = "Organizational"
    ) -> Dict[str, Any]:
        """
        Create a new connection.

        Args:
            display_name: Connection display name
            connectivity_type: Type of connectivity (ShareableCloud, etc.)
            data_source_type: Type of data source (AzureBlobStorage, etc.)
            connection_path: Path/URL to the data source
            credential_type: Type of credentials (Key, ServicePrincipal, etc.)
            credentials: Credential details based on credential_type
            privacy_level: Privacy level (Organizational, Private, Public)

        Returns:
            Dict with connection_id and creation info
        """
        endpoint = "/connections"

        payload = {
            "connectivityType": connectivity_type.value,
            "connectionDetails": {
                "type": data_source_type.value,
                "path": connection_path
            },
            "displayName": display_name,
            "privacyLevel": privacy_level,
            "credentialDetails": {
                "credentialType": credential_type.value,
                **credentials
            }
        }

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201])

        logger.info(f"Connection created: {result.get('id', display_name)}")

        return {
            "success": True,
            "connection_id": result.get("id"),
            "connection_name": display_name
        }

    async def create_azure_blob_connection(
        self,
        display_name: str,
        storage_account_name: str,
        account_key: str
    ) -> Dict[str, Any]:
        """
        Create an Azure Blob Storage connection with account key.

        Args:
            display_name: Connection display name
            storage_account_name: Storage account name
            account_key: Storage account key

        Returns:
            Dict with connection creation result
        """
        connection_path = f"https://{storage_account_name}.blob.core.windows.net"

        return await self.create_connection(
            display_name=display_name,
            connectivity_type=ConnectivityType.SHAREABLE_CLOUD,
            data_source_type=DataSourceType.AZURE_BLOB_STORAGE,
            connection_path=connection_path,
            credential_type=CredentialType.KEY,
            credentials={"key": account_key}
        )

    async def create_adls_gen2_connection(
        self,
        display_name: str,
        storage_account_name: str,
        account_key: str
    ) -> Dict[str, Any]:
        """
        Create an ADLS Gen2 connection with account key.

        Args:
            display_name: Connection display name
            storage_account_name: Storage account name
            account_key: Storage account key

        Returns:
            Dict with connection creation result
        """
        connection_path = f"https://{storage_account_name}.dfs.core.windows.net"

        return await self.create_connection(
            display_name=display_name,
            connectivity_type=ConnectivityType.SHAREABLE_CLOUD,
            data_source_type=DataSourceType.AZURE_DATA_LAKE_STORAGE,
            connection_path=connection_path,
            credential_type=CredentialType.KEY,
            credentials={"key": account_key}
        )

    async def create_service_principal_connection(
        self,
        display_name: str,
        data_source_type: DataSourceType,
        connection_path: str,
        tenant_id: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Create a connection using service principal authentication.

        Args:
            display_name: Connection display name
            data_source_type: Type of data source
            connection_path: Path/URL to the data source
            tenant_id: Azure AD tenant ID
            client_id: Service principal client ID
            client_secret: Service principal secret

        Returns:
            Dict with connection creation result
        """
        return await self.create_connection(
            display_name=display_name,
            connectivity_type=ConnectivityType.SHAREABLE_CLOUD,
            data_source_type=data_source_type,
            connection_path=connection_path,
            credential_type=CredentialType.SERVICE_PRINCIPAL,
            credentials={
                "tenantId": tenant_id,
                "servicePrincipalClientId": client_id,
                "servicePrincipalSecret": client_secret
            }
        )

    async def delete_connection(self, connection_id: str) -> Dict[str, Any]:
        """Delete a connection."""
        endpoint = f"/connections/{connection_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            return {"success": True, "connection_id": connection_id}
        else:
            raise Exception(f"Failed to delete connection: {response.text}")
