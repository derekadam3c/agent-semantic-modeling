"""SQL INFORMATION_SCHEMA parser."""

from typing import Dict, Any


class SQLSchemaParser:
    """Parse SQL INFORMATION_SCHEMA exports."""
    
    def parse(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse SQL schema metadata."""
        raise NotImplementedError
