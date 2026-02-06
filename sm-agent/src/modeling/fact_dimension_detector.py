"""Fact and dimension table detection."""

from typing import Dict, Any, List
from enum import Enum


class TableType(Enum):
    """Table type classification."""
    FACT = "fact"
    DIMENSION = "dimension"
    UNCERTAIN = "uncertain"


class FactDimensionDetector:
    """Detect fact and dimension tables from schema."""
    
    def classify_table(self, table_metadata: Dict[str, Any]) -> TableType:
        """Classify a table as fact, dimension, or uncertain."""
        raise NotImplementedError
        
    def identify_grain(self, table_metadata: Dict[str, Any]) -> List[str]:
        """Identify the grain (key columns) of a fact table."""
        raise NotImplementedError
        
    def detect_natural_keys(self, table_metadata: Dict[str, Any]) -> List[str]:
        """Detect natural keys for dimension tables."""
        raise NotImplementedError
