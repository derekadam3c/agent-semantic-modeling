"""Hierarchy detection and builder."""

from typing import Dict, Any, List
from pydantic import BaseModel


class Hierarchy(BaseModel):
    """Power BI hierarchy definition."""
    name: str
    table: str
    levels: List[str]  # Column names in hierarchy order


class HierarchyBuilder:
    """Build hierarchies for dimension tables."""
    
    def detect_date_hierarchies(self, table: Dict[str, Any]) -> List[Hierarchy]:
        """Detect date hierarchies (Year > Quarter > Month > Day)."""
        raise NotImplementedError
        
    def detect_geographic_hierarchies(self, table: Dict[str, Any]) -> List[Hierarchy]:
        """Detect geographic hierarchies (Country > State > City)."""
        raise NotImplementedError
        
    def detect_custom_hierarchies(self, table: Dict[str, Any]) -> List[Hierarchy]:
        """Detect custom hierarchies from column patterns."""
        raise NotImplementedError
