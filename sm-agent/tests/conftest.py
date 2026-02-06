"""Test fixtures and configuration."""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_csv_schema():
    """Sample CSV schema for testing."""
    return {
        "tables": [
            {
                "name": "Sales",
                "columns": [
                    {"name": "SalesID", "type": "int", "nullable": False},
                    {"name": "ProductID", "type": "int", "nullable": False},
                    {"name": "CustomerID", "type": "int", "nullable": False},
                    {"name": "OrderDate", "type": "date", "nullable": False},
                    {"name": "SalesAmount", "type": "decimal", "nullable": False},
                    {"name": "Quantity", "type": "int", "nullable": False}
                ]
            },
            {
                "name": "Product",
                "columns": [
                    {"name": "ProductID", "type": "int", "nullable": False},
                    {"name": "ProductName", "type": "varchar", "nullable": False},
                    {"name": "Category", "type": "varchar", "nullable": True},
                    {"name": "UnitPrice", "type": "decimal", "nullable": False}
                ]
            }
        ]
    }


@pytest.fixture
def mock_fabric_client(mocker):
    """Mock Fabric API client."""
    mock = mocker.Mock()
    mock.get_workspace.return_value = {"id": "test-ws-123", "name": "Test Workspace"}
    return mock
