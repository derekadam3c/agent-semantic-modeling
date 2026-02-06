"""Performance heuristics and analysis."""

from typing import Dict, Any, List
from pydantic import BaseModel


class PerformanceWarning(BaseModel):
    """Performance warning."""
    category: str
    severity: str
    message: str
    recommendation: str
    affected_objects: List[str]


class PerformanceAnalyzer:
    """Analyze model for performance issues."""
    
    def analyze_measure_complexity(self, model: Dict[str, Any]) -> List[PerformanceWarning]:
        """Analyze DAX measure complexity."""
        raise NotImplementedError
        
    def analyze_relationship_cardinality(
        self,
        model: Dict[str, Any]
    ) -> List[PerformanceWarning]:
        """Analyze relationship cardinality impact."""
        raise NotImplementedError
        
    def analyze_direct_lake_compatibility(
        self,
        model: Dict[str, Any]
    ) -> List[PerformanceWarning]:
        """Check Direct Lake optimization compatibility."""
        raise NotImplementedError
        
    def estimate_memory_footprint(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate model memory footprint."""
        raise NotImplementedError
