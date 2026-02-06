"""Tests for fact/dimension detection."""

import pytest
from src.modeling.fact_dimension_detector import (
    FactDimensionDetector,
    TableType
)


class TestFactDimensionDetector:
    """Test suite for fact/dimension detection."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return FactDimensionDetector()
    
    def test_classify_fact_table(self, detector):
        """Test fact table classification."""
        # Fact table: many numeric columns, foreign keys
        table_metadata = {
            "name": "Sales",
            "columns": [
                {"name": "SalesAmount", "type": "decimal"},
                {"name": "Quantity", "type": "int"},
                {"name": "ProductKey", "type": "int"},
                {"name": "DateKey", "type": "int"}
            ]
        }
        assert detector.classify_table(table_metadata) == TableType.FACT
    
    def test_classify_dimension_table(self, detector):
        """Test dimension table classification."""
        # Dimension table: descriptive columns, natural key
        table_metadata = {
            "name": "Product",
            "columns": [
                {"name": "ProductKey", "type": "int"},
                {"name": "ProductName", "type": "varchar"},
                {"name": "Category", "type": "varchar"},
                {"name": "SubCategory", "type": "varchar"}
            ]
        }
        assert detector.classify_table(table_metadata) == TableType.DIMENSION
