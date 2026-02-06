"""Relationship inference and builder."""

from typing import Dict, Any, List
from pydantic import BaseModel


class Relationship(BaseModel):
    """Power BI relationship definition."""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str  # "OneToMany", "ManyToOne", "OneToOne"
    cross_filter_direction: str  # "Single", "Both"
    is_active: bool = True


class RelationshipBuilder:
    """Build relationships between tables."""
    
    def infer_relationships(
        self,
        tables: List[Dict[str, Any]]
    ) -> List[Relationship]:
        """Infer relationships from table schemas."""
        raise NotImplementedError
        
    def detect_circular_dependencies(
        self,
        relationships: List[Relationship]
    ) -> List[str]:
        """Detect circular relationship patterns (anti-pattern)."""
        raise NotImplementedError
