"""
Pydantic schemas for Agent Invocation Handler request/response contracts.

This module defines the data models for the POST /invoke endpoint, including:
- Request schemas with discriminated union for schema sources
- Response schemas with TMSL artifacts and validation results
- Error response schemas following RFC 7807 Problem Details
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# Enums
# ============================================================================


class DeploymentMode(str, Enum):
    """Deployment mode for semantic model."""

    DRY_RUN = "dry_run"
    VALIDATE_ONLY = "validate_only"
    AUTO_DEPLOY = "auto_deploy"


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class StepStatus(str, Enum):
    """Status of individual workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationSeverity(str, Enum):
    """Severity level for validation results."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationCategory(str, Enum):
    """Category of validation finding."""

    ANTI_PATTERN = "anti_pattern"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"


class ResponseStatus(str, Enum):
    """Overall response status."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    VALIDATION_ERROR = "validation_error"
    WORKFLOW_ERROR = "workflow_error"
    TIMEOUT = "timeout"


class DeploymentStatus(str, Enum):
    """Deployment lifecycle status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TargetOptimization(str, Enum):
    """Target optimization mode for semantic model."""

    IMPORT = "import"
    DIRECT_QUERY = "direct_query"
    DIRECT_LAKE = "direct_lake"


# ============================================================================
# Schema Source (Discriminated Union)
# ============================================================================


class CsvUrlSource(BaseModel):
    """CSV URL schema source."""

    type: Literal["csv_url"] = "csv_url"
    url: HttpUrl = Field(..., description="URL to CSV file")
    sample_rows: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Number of rows to sample (default: all)",
    )


class SqlJsonSource(BaseModel):
    """SQL schema JSON source (INFORMATION_SCHEMA export)."""

    type: Literal["sql_json"] = "sql_json"
    tables: list[dict[str, Any]] = Field(
        ..., description="Table metadata from INFORMATION_SCHEMA"
    )
    columns: list[dict[str, Any]] = Field(
        ..., description="Column metadata from INFORMATION_SCHEMA"
    )
    foreign_keys: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Foreign key constraints"
    )


class LakehouseSource(BaseModel):
    """Fabric Lakehouse schema source."""

    type: Literal["lakehouse_connection"] = "lakehouse_connection"
    workspace_id: UUID = Field(..., description="Fabric workspace ID")
    item_id: UUID = Field(..., description="Lakehouse item ID")
    table_filter: Optional[list[str]] = Field(
        default=None, description="Optional table name filter (regex patterns)"
    )


# Discriminated union for schema sources
SchemaSource = Union[CsvUrlSource, SqlJsonSource, LakehouseSource]


# ============================================================================
# Request Models
# ============================================================================


class ProcessingOptions(BaseModel):
    """Optional processing configuration."""

    detect_measures: bool = Field(default=True, description="Auto-detect measures")
    detect_hierarchies: bool = Field(
        default=True, description="Auto-detect hierarchies"
    )
    target_optimization: Optional[TargetOptimization] = Field(
        default=None, description="Target query optimization mode"
    )
    approval_required: bool = Field(
        default=False,
        description="Require approval before deployment (only for auto_deploy mode)",
    )


class InvocationRequest(BaseModel):
    """Request schema for POST /invoke endpoint."""

    correlation_id: Optional[UUID] = Field(
        default_factory=uuid4,
        description="Correlation ID for request tracing (auto-generated if not provided)",
    )
    schema_source: SchemaSource = Field(
        ..., discriminator="type", description="Schema source configuration"
    )
    workspace_id: UUID = Field(
        ..., description="Target Fabric workspace ID for deployment"
    )
    deployment_mode: DeploymentMode = Field(
        ..., description="Deployment mode (dry_run, validate_only, auto_deploy)"
    )
    options: Optional[ProcessingOptions] = Field(
        default_factory=ProcessingOptions, description="Processing options"
    )

    @field_validator("deployment_mode")
    @classmethod
    def validate_deployment_mode(cls, v: DeploymentMode) -> DeploymentMode:
        """Validate deployment mode is a valid enum value."""
        if v not in DeploymentMode:
            raise ValueError(
                f"deployment_mode must be one of: {', '.join([m.value for m in DeploymentMode])}"
            )
        return v


# ============================================================================
# Response Models
# ============================================================================


class TMSLArtifact(BaseModel):
    """Generated TMSL (Tabular Model Scripting Language) artifact."""

    model_name: str = Field(..., description="Semantic model name")
    version: str = Field(default="1.0", description="TMSL version")
    tables: list[dict[str, Any]] = Field(
        default_factory=list, description="Table definitions"
    )
    relationships: list[dict[str, Any]] = Field(
        default_factory=list, description="Relationship definitions"
    )
    measures: list[dict[str, Any]] = Field(
        default_factory=list, description="Measure definitions"
    )
    hierarchies: list[dict[str, Any]] = Field(
        default_factory=list, description="Hierarchy definitions"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ValidationResult(BaseModel):
    """Validation finding from model validation step."""

    severity: ValidationSeverity = Field(..., description="Severity level")
    category: ValidationCategory = Field(..., description="Validation category")
    message: str = Field(..., description="Human-readable message")
    affected_objects: list[str] = Field(
        default_factory=list, description="Affected tables/columns/relationships"
    )
    recommendation: Optional[str] = Field(
        default=None, description="Remediation recommendation"
    )


class DeploymentStatusDetail(BaseModel):
    """Deployment status information."""

    deployment_id: Optional[str] = Field(
        default=None, description="Fabric deployment ID"
    )
    status: DeploymentStatus = Field(..., description="Deployment status")
    workspace_id: UUID = Field(..., description="Target workspace ID")
    model_name: str = Field(..., description="Deployed model name")
    deployment_type: Literal["full", "incremental"] = Field(
        default="full", description="Deployment type"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Deployment start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Deployment completion time"
    )


class WorkflowStepSummary(BaseModel):
    """Summary of a single workflow step execution."""

    step_name: str = Field(
        ..., description="Step name (parse, classify, relationships, etc.)"
    )
    step_number: int = Field(..., ge=1, le=8, description="Step number (1-8)")
    status: StepStatus = Field(..., description="Step status")
    duration_ms: Optional[int] = Field(
        default=None, ge=0, description="Step duration in milliseconds"
    )
    record_count: Optional[int] = Field(
        default=None, ge=0, description="Number of records processed"
    )


class ExecutionSummary(BaseModel):
    """Workflow execution summary."""

    execution_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique execution ID"
    )
    status: WorkflowStatus = Field(..., description="Workflow status")
    total_steps: int = Field(default=8, ge=1, description="Total workflow steps")
    completed_steps: int = Field(default=0, ge=0, description="Completed steps")
    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Workflow start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Workflow completion time"
    )
    duration_ms: Optional[int] = Field(
        default=None, ge=0, description="Total duration in milliseconds"
    )
    steps: list[WorkflowStepSummary] = Field(
        default_factory=list, description="Step-by-step execution details"
    )


class ErrorDetail(BaseModel):
    """RFC 7807 Problem Details error information."""

    type: str = Field(
        ...,
        description="URI reference identifying the problem type (RFC 7807)",
    )
    title: str = Field(..., description="Short, human-readable summary")
    status: int = Field(..., ge=400, le=599, description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation")
    instance: str = Field(
        default="/invoke", description="URI reference identifying the occurrence"
    )
    correlation_id: Optional[UUID] = Field(
        default=None, description="Request correlation ID"
    )
    workflow_step: Optional[str] = Field(
        default=None, description="Failed workflow step name"
    )
    failed_at: Optional[datetime] = Field(
        default=None, description="Failure timestamp"
    )
    remediation: Optional[str] = Field(
        default=None, description="Suggested remediation steps"
    )
    affected_objects: Optional[list[str]] = Field(
        default=None, description="Affected entities (tables, columns, etc.)"
    )


class InvocationResponse(BaseModel):
    """Response schema for POST /invoke endpoint."""

    correlation_id: UUID = Field(..., description="Request correlation ID")
    status: ResponseStatus = Field(..., description="Overall response status")
    tmsl_output: Optional[TMSLArtifact] = Field(
        default=None, description="Generated TMSL artifact (on success)"
    )
    validation_results: list[ValidationResult] = Field(
        default_factory=list, description="Model validation findings"
    )
    deployment_status: Optional[DeploymentStatusDetail] = Field(
        default=None, description="Deployment status (if deployment initiated)"
    )
    execution_summary: ExecutionSummary = Field(
        ..., description="Workflow execution summary"
    )
    error_detail: Optional[ErrorDetail] = Field(
        default=None, description="Error details (if failed)"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Response generation timestamp"
    )


# ============================================================================
# Error Response Models (RFC 7807)
# ============================================================================


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details for HTTP APIs."""

    type: str = Field(
        ...,
        description="URI reference identifying the problem type",
        example="https://agent.fabric.microsoft.com/errors/validation-error",
    )
    title: str = Field(
        ..., description="Short, human-readable summary", example="Validation Error"
    )
    status: int = Field(
        ...,
        ge=400,
        le=599,
        description="HTTP status code",
        example=400,
    )
    detail: str = Field(
        ...,
        description="Human-readable explanation",
        example="schema_source is required",
    )
    instance: str = Field(
        ...,
        description="URI reference identifying the occurrence",
        example="/invoke",
    )
    correlation_id: Optional[UUID] = Field(
        default=None, description="Request correlation ID for tracing"
    )
    # Extension fields
    field_errors: Optional[dict[str, str]] = Field(
        default=None, description="Field-level validation errors"
    )
    workflow_step: Optional[str] = Field(
        default=None, description="Failed workflow step (for workflow errors)"
    )
    failed_at: Optional[datetime] = Field(
        default=None, description="Failure timestamp"
    )
    remediation: Optional[str] = Field(
        default=None, description="Suggested remediation"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "type": "https://agent.fabric.microsoft.com/errors/validation-error",
                "title": "Request Validation Failed",
                "status": 400,
                "detail": "schema_source field is required",
                "instance": "/invoke",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "field_errors": {"schema_source": "field required"},
            }
        }
