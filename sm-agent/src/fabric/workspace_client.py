"""Microsoft Fabric workspace client for access validation.

Provides workspace validation and access checking using Azure managed identity
to authenticate with Fabric APIs.
"""

import httpx
from typing import Dict, Any, List, Optional
from uuid import UUID

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken

from ..core.config import settings
from ..core.logging import get_logger, log_exception


logger = get_logger(__name__)


class WorkspaceAccessError(Exception):
    """Raised when agent lacks required workspace permissions."""
    
    def __init__(self, workspace_id: UUID, message: str, required_role: str = "Fabric Workspace Admin or Contributor"):
        self.workspace_id = workspace_id
        self.message = message
        self.required_role = required_role
        super().__init__(message)


class FabricWorkspaceClient:
    """Client for validating Fabric workspace access and operations.
    
    Uses managed identity or service principal to authenticate with Fabric APIs
    and validate agent has required permissions to deploy semantic models.
    """
    
    # Fabric API scopes for authentication
    FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
    
    def __init__(self, credential: Optional[DefaultAzureCredential] = None):
        """Initialize workspace client.
        
        Args:
            credential: Optional Azure credential (defaults to DefaultAzureCredential)
        """
        self.credential = credential or DefaultAzureCredential()
        self.base_url = settings.fabric_api_endpoint
        self.http_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(10.0),
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(
            "Fabric workspace client initialized",
            extra={
                "endpoint": self.base_url,
                "auth_method": "managed_identity" if settings.use_managed_identity else "service_principal"
            }
        )
    
    async def _get_access_token(self) -> str:
        """Get access token for Fabric API.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token acquisition fails
        """
        try:
            # Get token synchronously (Azure SDK doesn't support async yet)
            token: AccessToken = self.credential.get_token(self.FABRIC_SCOPE)
            logger.debug("Fabric access token acquired")
            return token.token
        except Exception as e:
            log_exception(logger, e, operation="get_fabric_token")
            raise
    
    async def validate_access(self, workspace_id: UUID) -> bool:
        """Validate agent has access to specified Fabric workspace.
        
        Makes a GET request to Fabric API to check workspace exists and
        agent identity has permissions to access it.
        
        Args:
            workspace_id: Fabric workspace ID to validate
            
        Returns:
            True if access is granted
            
        Raises:
            WorkspaceAccessError: If access is denied or workspace doesn't exist
            Exception: For other API errors
        """
        logger.info(f"Validating access to Fabric workspace: {workspace_id}")
        
        try:
            # Get access token
            token = await self._get_access_token()
            
            # Call Fabric API to get workspace details
            # Endpoint: GET /v1/workspaces/{workspaceId}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = await self.http_client.get(
                f"/workspaces/{workspace_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                workspace_data = response.json()
                logger.info(
                    f"Workspace access validated: {workspace_id}",
                    extra={
                        "workspace_id": str(workspace_id),
                        "workspace_name": workspace_data.get("displayName", "Unknown")
                    }
                )
                return True
            
            elif response.status_code == 403:
                # Permission denied
                logger.warning(
                    f"Workspace access denied: {workspace_id}",
                    extra={
                        "workspace_id": str(workspace_id),
                        "status_code": 403
                    }
                )
                raise WorkspaceAccessError(
                    workspace_id=workspace_id,
                    message=(
                        f"Agent does not have permission to access workspace {workspace_id}. "
                        f"Grant the agent's managed identity the required role on the workspace."
                    ),
                    required_role="Fabric Workspace Admin or Fabric Contributor"
                )
            
            elif response.status_code == 404:
                # Workspace not found
                logger.warning(
                    f"Workspace not found: {workspace_id}",
                    extra={"workspace_id": str(workspace_id)}
                )
                raise WorkspaceAccessError(
                    workspace_id=workspace_id,
                    message=f"Workspace {workspace_id} does not exist or is not accessible"
                )
            
            else:
                # Other error
                logger.error(
                    f"Fabric API error: {response.status_code}",
                    extra={
                        "workspace_id": str(workspace_id),
                        "status_code": response.status_code,
                        "response": response.text
                    }
                )
                response.raise_for_status()
                
        except WorkspaceAccessError:
            # Re-raise workspace access errors
            raise
        except httpx.HTTPStatusError as e:
            log_exception(
                logger,
                e,
                workspace_id=str(workspace_id),
                status_code=e.response.status_code
            )
            raise
        except Exception as e:
            log_exception(logger, e, workspace_id=str(workspace_id), operation="validate_workspace_access")
            raise
        
        return True
    
    async def get_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Get workspace metadata.
        
        Args:
            workspace_id: Fabric workspace ID
            
        Returns:
            Workspace metadata dictionary
        """
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.http_client.get(
            f"/workspaces/{workspace_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
        
    async def list_semantic_models(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List semantic models in workspace.
        
        Args:
            workspace_id: Fabric workspace ID
            
        Returns:
            List of semantic model metadata dictionaries
        """
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await self.http_client.get(
            f"/workspaces/{workspace_id}/semanticModels",
            headers=headers
        )
        response.raise_for_status()
        return response.json().get("value", [])
        
    async def validate_permissions(self, workspace_id: str) -> Dict[str, Any]:
        """Validate deployment permissions.
        
        Args:
            workspace_id: Fabric workspace ID
        
        Returns:
            Permission validation results
        """
        # Use validate_access for permission checking
        await self.validate_access(UUID(workspace_id))
        return {"has_access": True, "workspace_id": workspace_id}
    
    async def close(self):
        """Close HTTP client and cleanup resources."""
        await self.http_client.aclose()


# Global client instance
_client: Optional[FabricWorkspaceClient] = None


def get_workspace_client() -> FabricWorkspaceClient:
    """Get or create global WorkspaceClient instance."""
    global _client
    if _client is None:
        _client = FabricWorkspaceClient()
    return _client


async def close_workspace_client():
    """Close global workspace client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None

