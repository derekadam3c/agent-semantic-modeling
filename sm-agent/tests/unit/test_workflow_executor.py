"""Smoke tests for workflow executor (happy path only)."""

import pytest
from src.orchestration.workflow_executor import WorkflowExecutor
from src.core.schemas import (
    InvocationRequest,
    CsvUrlSource,
    ProcessingOptions,
    DeploymentMode,
    WorkflowStatus,
)


class TestWorkflowExecutor:
    """Smoke tests for WorkflowExecutor class."""

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """Test workflow executor initialization."""
        executor = WorkflowExecutor()

        assert executor is not None
        assert hasattr(executor, "execute")

    @pytest.mark.asyncio
    async def test_csv_workflow_execution(self):
        """Test basic CSV workflow execution (placeholder steps)."""
        from uuid import UUID
        
        executor = WorkflowExecutor()

        request = InvocationRequest(
            schema_source=CsvUrlSource(
                type="csv_url",
                url="https://example.com/data.csv",
                sample_rows=100,
            ),
            workspace_id=UUID("00000000-0000-0000-0000-000000000000"),
            deployment_mode=DeploymentMode.DRY_RUN,
            options=ProcessingOptions(
                detect_measures=True,
                detect_hierarchies=True,
            ),
        )

        result, summary = await executor.execute(
            request=request,
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
        )

        # Since steps are placeholders, we expect completion
        assert result is not None
        assert summary.status in [WorkflowStatus.COMPLETED, WorkflowStatus.PENDING]
        assert summary.total_steps == 8  # All 8 workflow steps

    @pytest.mark.asyncio
    async def test_sql_workflow_execution(self):
        """Test basic SQL workflow routing."""
        from src.core.schemas import SqlJsonSource
        from uuid import UUID

        executor = WorkflowExecutor()

        request = InvocationRequest(
            schema_source=SqlJsonSource(
                type="sql_json",
                tables=[{"name": "Sales"}],
                columns=[{"name": "SalesID", "table": "Sales"}],
            ),
            workspace_id=UUID("00000000-0000-0000-0000-000000000000"),
            deployment_mode=DeploymentMode.VALIDATE_ONLY,
        )

        result, summary = await executor.execute(
            request=request,
            correlation_id=UUID("00000000-0000-0000-0000-000000000123"),
        )

        assert result is not None
        assert summary.total_steps > 0
