"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Azure AI Foundry
    foundry_endpoint: Optional[str] = None
    foundry_subscription_id: Optional[str] = None
    foundry_resource_group: Optional[str] = None
    foundry_project_name: Optional[str] = None
    
    # Fabric
    fabric_tenant_id: Optional[str] = None
    fabric_default_workspace_id: Optional[str] = None
    
    # Authentication
    use_managed_identity: bool = True
    
    # Deployment
    require_approval_for_production: bool = True
    dry_run_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
