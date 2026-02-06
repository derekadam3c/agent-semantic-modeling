"""Tests for anti-pattern detection."""

import pytest
from src.validation.anti_pattern_detector import (
    AntiPatternDetector,
    AntiPattern
)


class TestAntiPatternDetector:
    """Test suite for anti-pattern detection."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return AntiPatternDetector()
    
    def test_detect_circular_relationships(self, detector):
        """Test circular relationship detection."""
        model = {
            "relationships": [
                {"from": "A", "to": "B"},
                {"from": "B", "to": "C"},
                {"from": "C", "to": "A"}  # Circular!
            ]
        }
        findings = detector.check_circular_relationships(model)
        assert len(findings) > 0
        assert findings[0].severity == "error"
    
    def test_detect_wide_tables(self, detector):
        """Test wide table detection."""
        model = {
            "tables": [
                {
                    "name": "WideTable",
                    "columns": [f"Col{i}" for i in range(150)]  # 150 columns
                }
            ]
        }
        findings = detector.check_wide_tables(model)
        assert len(findings) > 0
        assert "WideTable" in findings[0].affected_objects
