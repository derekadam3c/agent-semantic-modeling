"""Application configuration with Pydantic Settings.

Loads configuration from environment variables and .env file.
Supports managed identity authentication for Azure services.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Power BI Semantic Modeling Agent.
    
    Configuration is loaded from environment variables and .env file.
    All Azure-related settings support managed identity authentication.
    """
    
    # =============================================================================
    # Azure Identity Configuration
    # =============================================================================
    azure_client_id: Optional[str] = Field(
        default=None,
        description="Azure AD Client ID for service principal or managed identity"
    )
    azure_tenant_id: Optional[str] = Field(
        default=None,
        description="Azure AD Tenant ID"
    )
    azure_client_secret: Optional[str] = Field(
        default=None,
        description="Azure AD Client Secret (not used with managed identity)"
    )
    use_managed_identity: bool = Field(
        default=True,
        description="Use Azure managed identity for authentication instead of service principal"
    )
    
    # =============================================================================
    # Azure AI Foundry Configuration
    # =============================================================================
    foundry_project_id: Optional[str] = Field(
        default=None,
        description="Azure AI Foundry project ID (optional - only needed for agent registration)"
    )
    foundry_endpoint: str = Field(
        default="https://api.azure.com",
        description="Azure AI Foundry API endpoint"
    )
    foundry_subscription_id: Optional[str] = Field(
        default=None,
        description="Azure subscription ID where Foundry project is deployed"
    )
    foundry_resource_group: Optional[str] = Field(
        default=None,
        description="Azure resource group containing Foundry project"
    )
    foundry_project_name: Optional[str] = Field(
        default=None,
        description="Azure AI Foundry project name"
    )
    
    # =============================================================================
    # Microsoft Fabric Configuration
    # =============================================================================
    fabric_workspace_id: Optional[str] = Field(
        default=None,
        description="Default Microsoft Fabric workspace ID for deployments"
    )
    fabric_tenant_id: Optional[str] = Field(
        default=None,
        description="Microsoft Fabric tenant ID"
    )
    fabric_api_endpoint: str = Field(
        default="https://api.fabric.microsoft.com/v1",
        description="Microsoft Fabric API endpoint"
    )
    
    # =============================================================================
    # Application Insights Configuration
    # =============================================================================
    app_insights_connection_string: Optional[str] = Field(
        default=None,
        alias="applicationinsights_connection_string",
        description="Application Insights connection string for telemetry"
    )
    app_insights_instrumentation_key: Optional[str] = Field(
        default=None,
        description="Application Insights instrumentation key (legacy)"
    )
    
    # =============================================================================
    # Application Configuration
    # =============================================================================
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    dry_run_enabled: bool = Field(
        default=True,
        description="Enable dry-run mode to preview changes without deploying"
    )
    require_approval_for_production: bool = Field(
        default=True,
        description="Require manual approval before production deployments"
    )
    version: str = Field(
        default="1.0.0",
        description="Agent version"
    )
    
    # =============================================================================
    # HTTP Server Configuration
    # =============================================================================
    host: str = Field(
        default="0.0.0.0",
        description="HTTP server host address"
    )
    port: int = Field(
        default=8000,
        description="HTTP server port"
    )
    
    # =============================================================================
    # Validation
    # =============================================================================
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {v}")
        return v_upper
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is a known value."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}, got {v}")
        return v_lower
    
    # =============================================================================
    # Pydantic Configuration
    # =============================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True
    )


# Global settings instance
settings = Settings()
