"""Pydantic models for agent request/response schemas.

Models defined according to OpenAPI specification in:
specs/001-foundry-agent-registration/contracts/agent-api.yaml
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


# =============================================================================
# Enumerations
# =============================================================================

class HealthStatus(str, Enum):
    """Overall health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealthStatus(str, Enum):
    """Component-level health status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DeploymentMode(str, Enum):
    """Deployment execution mode."""
    DRY_RUN = "dry_run"
    DEPLOY = "deploy"


class InvocationStatus(str, Enum):
    """Agent invocation execution status."""
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TargetOptimization(str, Enum):
    """Target data access mode for optimization."""
    DIRECT_LAKE = "direct_lake"
    IMPORT = "import"
    DIRECT_QUERY = "direct_query"


class SchemaSourceType(str, Enum):
    """Type discriminator for schema sources."""
    CSV_URL = "csv_url"
    LAKEHOUSE_SCHEMA = "lakehouse_schema"
    SQL_SCHEMA = "sql_schema"


# =============================================================================
# Schema Source Models
# =============================================================================

class CsvSchemaSource(BaseModel):
    """CSV file schema source.
    
    Provides schema and sample data from a publicly accessible CSV URL.
    """
    type: Literal[SchemaSourceType.CSV_URL] = Field(
        default=SchemaSourceType.CSV_URL,
        description="Schema source type discriminator"
    )
    url: HttpUrl = Field(
        description="Publicly accessible URL to CSV file with schema and sample data"
    )
    sample_rows: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Number of sample rows to analyze for type inference"
    )


class LakehouseSchemaSource(BaseModel):
    """Fabric Lakehouse schema source.
    
    Extracts schema from tables in a Fabric Lakehouse.
    """
    type: Literal[SchemaSourceType.LAKEHOUSE_SCHEMA] = Field(
        default=SchemaSourceType.LAKEHOUSE_SCHEMA,
        description="Schema source type discriminator"
    )
    workspace_id: UUID = Field(
        description="Fabric workspace containing the lakehouse"
    )
    lakehouse_id: UUID = Field(
        description="Lakehouse ID to extract schema from"
    )


class SqlSchemaSource(BaseModel):
    """SQL database schema source.
    
    Connects to SQL database and extracts table schema.
    """
    type: Literal[SchemaSourceType.SQL_SCHEMA] = Field(
        default=SchemaSourceType.SQL_SCHEMA,
        description="Schema source type discriminator"
    )
    connection_string: str = Field(
        description="SQL database connection string (credentials via managed identity or Key Vault reference)"
    )
    schema_name: str = Field(
        default="dbo",
        description="SQL schema name to extract from"
    )


# Union type for schema sources with discriminator
SchemaSource = Union[CsvSchemaSource, LakehouseSchemaSource, SqlSchemaSource]


# =============================================================================
# Request Models
# =============================================================================

class ModelingOptions(BaseModel):
    """Optional modeling configuration parameters."""
    
    detect_measures: bool = Field(
        default=True,
        description="Automatically detect and generate measure definitions"
    )
    detect_hierarchies: bool = Field(
        default=True,
        description="Automatically detect and generate dimension hierarchies"
    )
    target_optimization: TargetOptimization = Field(
        default=TargetOptimization.DIRECT_LAKE,
        description="Target data access mode for optimization recommendations"
    )


class InvocationRequest(BaseModel):
    """Agent invocation request payload.
    
    Specifies schema source, target workspace, deployment mode, and options.
    """
    
    schema_source: SchemaSource = Field(
        description="Schema source configuration (CSV, Lakehouse, or SQL)",
        discriminator="type"
    )
    workspace_id: UUID = Field(
        description="Target Fabric workspace ID for deployment"
    )
    deployment_mode: DeploymentMode = Field(
        description=(
            "dry_run: Generate artifacts and validation report without deploying. "
            "deploy: Execute deployment to Fabric workspace"
        )
    )
    options: Optional[ModelingOptions] = Field(
        default=None,
        description="Optional modeling configuration"
    )


# =============================================================================
# Response Models
# =============================================================================

class HealthChecks(BaseModel):
    """Individual health check results."""
    
    application: ComponentHealthStatus = Field(
        description="Application runtime status"
    )
    fabric_connectivity: ComponentHealthStatus = Field(
        description="Connectivity to Fabric APIs"
    )
    memory_usage_mb: int = Field(
        ge=0,
        description="Current memory usage in megabytes"
    )
    uptime_seconds: int = Field(
        ge=0,
        description="Time since agent container started"
    )


class HealthResponse(BaseModel):
    """Health check response.
    
    Note: This is the OpenAPI schema version. The actual health endpoint
    uses an enhanced version with additional system information.
    """
    
    status: HealthStatus = Field(
        description="Overall agent health status"
    )
    version: str = Field(
        description="Semantic version of the deployed agent",
        pattern=r'^\d+\.\d+\.\d+$'
    )
    checks: HealthChecks = Field(
        description="Individual health check results"
    )
    timestamp: datetime = Field(
        description="Timestamp when health check was performed"
    )
    
    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be in format X.Y.Z, got {v}")
        return v


class ArtifactUrls(BaseModel):
    """URLs to generated semantic model artifacts."""
    
    tmsl_url: HttpUrl = Field(
        description="URL to generated TMSL file (valid for 24 hours)"
    )
    tmdl_url: HttpUrl = Field(
        description="URL to generated TMDL file (valid for 24 hours)"
    )
    validation_report_url: HttpUrl = Field(
        description="URL to validation report JSON (valid for 24 hours)"
    )


class DeploymentInfo(BaseModel):
    """Deployment result information.
    
    Only present when deployment_mode=deploy and deployment succeeded.
    """
    
    model_id: UUID = Field(
        description="Deployed semantic model ID in Fabric"
    )
    workspace_id: UUID = Field(
        description="Fabric workspace where model was deployed"
    )
    deployed_at: datetime = Field(
        description="Deployment completion timestamp"
    )


class Diagnostics(BaseModel):
    """Diagnostic information from semantic model generation."""
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking issues detected (e.g., high cardinality)"
    )
    anti_patterns: List[str] = Field(
        default_factory=list,
        description="Blocking anti-patterns that should be addressed"
    )


class InvocationResponse(BaseModel):
    """Agent invocation response payload."""
    
    invocation_id: UUID = Field(
        description="Unique identifier for this invocation"
    )
    status: InvocationStatus = Field(
        description="Final invocation status"
    )
    duration_ms: int = Field(
        ge=0,
        description="Total execution time in milliseconds"
    )
    artifacts: ArtifactUrls = Field(
        description="URLs to generated artifacts"
    )
    deployment: Optional[DeploymentInfo] = Field(
        default=None,
        description="Deployment information (only present when deployment_mode=deploy)"
    )
    diagnostics: Diagnostics = Field(
        description="Diagnostic information and warnings"
    )


class ErrorResponse(BaseModel):
    """Error response payload."""
    
    error_code: str = Field(
        description="Machine-readable error code",
        examples=["WORKSPACE_ACCESS_DENIED", "INVALID_REQUEST", "INTERNAL_ERROR", "TIMEOUT"]
    )
    error_message: str = Field(
        description="Human-readable error description"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional contextual information about the error"
    )
    timestamp: datetime = Field(
        description="Error occurrence timestamp"
    )
