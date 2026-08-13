"""
SQL Injection Prevention System

Provides comprehensive SQL injection attack prevention including:
- Parameterized query validation
- Dangerous SQL pattern detection
- Input sanitization and escaping
- Query builder with automatic parameterization
- Comment and string literal handling
- Prepared statement enforcement

Key Classes:
- SQLInjectionPrevention: Core SQL injection defense
- SafeQueryBuilder: Type-safe query construction
- SQLPatternDetector: Dangerous pattern recognition
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import re
from abc import ABC, abstractmethod


class SQLDangerPattern(Enum):
    """Common SQL injection attack patterns"""
    UNION_BASED = "union_based"
    BOOLEAN_BLIND = "boolean_blind"
    TIMED = "timed"
    ERROR_BASED = "error_based"
    STACKED_QUERIES = "stacked_queries"
    COMMENT_INJECTION = "comment_injection"
    WILDCARD_INJECTION = "wildcard_injection"


class QueryParamType(Enum):
    """Supported parameter types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    BLOB = "blob"


class SQLInjectionPrevention:
    """Core SQL injection prevention handler"""
    
    # Dangerous SQL keywords that could indicate injection
    DANGEROUS_KEYWORDS = {
        "union", "select", "insert", "update", "delete", "drop",
        "create", "alter", "truncate", "exec", "execute", "declare",
        "cast", "convert", "benchmark", "sleep", "waitfor", "pg_sleep",
        "sys.xp_", "sp_", "xp_", "dbcc", "sqlmap"
    }
    
    # SQL comment patterns
    COMMENT_PATTERNS = {
        r"--\s*$",  # SQL comment (line end)
        r"#",  # MySQL comment
        r"/\*.*?\*/",  # C-style comment
        r"--\s*.*?$",  # SQL comment with content
    }
    
    # Dangerous character combinations
    DANGEROUS_COMBOS = {
        r"'\s*(or|and|union|select)",  # String termination + logic
        r"\d\s*=\s*\d",  # Tautology (1=1)
        r"'\s*;\s*(drop|delete|update)",  # Command chaining
        r"\(.*select.*\)",  # Subquery injection
        r"benchmark\s*\(",  # Time-based blind
        r"sleep\s*\(",  # Sleep injection
        r"waitfor\s*delay",  # MSSQL time injection
        r"cast\s*\(",  # Type casting tricks
        r"convert\s*\(",  # Type conversion tricks
    }
    
    def __init__(self):
        """Initialize SQL injection prevention"""
        self.blocked_attempts: Dict[str, List[str]] = {}
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for performance"""
        patterns = {}
        
        # Compile comment patterns
        for pattern in self.COMMENT_PATTERNS:
            patterns[f"comment_{len(patterns)}"] = re.compile(
                pattern, re.IGNORECASE | re.MULTILINE
            )
        
        # Compile dangerous combos
        for pattern in self.DANGEROUS_COMBOS:
            patterns[f"combo_{len(patterns)}"] = re.compile(
                pattern, re.IGNORECASE
            )
        
        return patterns
    
    def detect_injection_pattern(self, input_str: str) -> Optional[SQLDangerPattern]:
        """
        Detect common SQL injection patterns
        
        Args:
            input_str: String to analyze
            
        Returns:
            SQLDangerPattern if dangerous pattern found, None otherwise
        """
        if not isinstance(input_str, str):
            return None
        
        input_lower = input_str.lower()
        
        # Detect UNION-based injection first (most specific)
        if re.search(r"union\s+select", input_lower):
            return SQLDangerPattern.UNION_BASED
        
        # Detect time-based blind (most specific)
        if re.search(r"(?:benchmark|sleep|waitfor)\s*\(", input_lower):
            return SQLDangerPattern.TIMED
        
        # Also detect MSSQL WAITFOR DELAY without parentheses
        if re.search(r"waitfor\s+delay", input_lower):
            return SQLDangerPattern.TIMED
        
        # Detect stacked queries
        if re.search(r";\s*(?:drop|delete|insert|update|create|truncate)", input_lower):
            return SQLDangerPattern.STACKED_QUERIES
        
        # Detect error-based injection
        if re.search(r"(?:extractvalue|updatexml|row_count|version|database)\s*\(", input_lower):
            return SQLDangerPattern.ERROR_BASED
        
        # Detect comment injection (before boolean/string patterns)
        if re.search(r"(?:--|#|/\*)", input_str):
            return SQLDangerPattern.COMMENT_INJECTION
        
        # Detect boolean blind (1=1, 1=2) - general OR/AND logic
        if re.search(r"(?:or|and)\s+\d\s*=\s*\d", input_lower):
            return SQLDangerPattern.BOOLEAN_BLIND
        
        # Detect wildcard injection
        if re.search(r"^%|%$|%%", input_str):
            return SQLDangerPattern.WILDCARD_INJECTION
        
        return None
    
    def contains_sql_keyword(self, input_str: str, strict: bool = True) -> bool:
        """
        Check if input contains SQL keywords indicating injection
        
        Args:
            input_str: String to check
            strict: If True, check for keywords even in strings
            
        Returns:
            True if dangerous keywords found
        """
        if not isinstance(input_str, str):
            return False
        
        input_lower = input_str.lower()
        
        # Find word boundaries for keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            # More lenient if not strict
            if strict:
                pattern = rf"\b{re.escape(keyword)}\b"
            else:
                pattern = re.escape(keyword)
            
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True
        
        return False
    
    def escape_sql_string(self, value: str, quote_char: str = "'") -> str:
        """
        Escape SQL string literal
        NOTE: This is a fallback - parameterized queries should be used!
        
        Args:
            value: String to escape
            quote_char: Quote character to use (' or ")
            
        Returns:
            Escaped string suitable for SQL
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Escape quote characters by doubling
        escaped = value.replace(quote_char, quote_char + quote_char)
        
        # Escape backslashes
        escaped = escaped.replace("\\", "\\\\")
        
        # Wrap in quotes
        return f"{quote_char}{escaped}{quote_char}"
    
    def validate_identifier(self, identifier: str) -> bool:
        """
        Validate SQL identifier (table name, column name)
        
        Args:
            identifier: Identifier to validate
            
        Returns:
            True if valid identifier, False otherwise
        """
        if not isinstance(identifier, str):
            return False
        
        # Identifiers should be alphanumeric + underscore
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
            return False
        
        # Check length (typical SQL limit is 64)
        if len(identifier) > 64:
            return False
        
        # Disallow SQL keywords as identifiers
        if identifier.lower() in self.DANGEROUS_KEYWORDS:
            return False
        
        return True
    
    def sanitize_table_name(self, table_name: str) -> str:
        """
        Sanitize table name for safe use
        
        Args:
            table_name: Table name to sanitize
            
        Returns:
            Sanitized table name or empty string if invalid
        """
        if not self.validate_identifier(table_name):
            return ""
        return table_name
    
    def sanitize_column_name(self, column_name: str) -> str:
        """
        Sanitize column name for safe use
        
        Args:
            column_name: Column name to sanitize
            
        Returns:
            Sanitized column name or empty string if invalid
        """
        if not self.validate_identifier(column_name):
            return ""
        return column_name
    
    def validate_parameter_value(
        self, value: Any, param_type: QueryParamType
    ) -> Tuple[bool, Any]:
        """
        Validate parameter value matches expected type
        
        Args:
            value: Value to validate
            param_type: Expected parameter type
            
        Returns:
            Tuple of (is_valid, sanitized_value)
        """
        try:
            if param_type == QueryParamType.STRING:
                if not isinstance(value, str):
                    value = str(value)
                return (True, value)
            
            elif param_type == QueryParamType.INTEGER:
                int_val = int(value)
                return (True, int_val)
            
            elif param_type == QueryParamType.FLOAT:
                float_val = float(value)
                return (True, float_val)
            
            elif param_type == QueryParamType.BOOLEAN:
                if isinstance(value, bool):
                    return (True, value)
                if isinstance(value, str):
                    return (True, value.lower() in ("true", "yes", "1"))
                return (True, bool(value))
            
            elif param_type == QueryParamType.DATE:
                # Basic ISO 8601 format check
                if not re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?Z?$", str(value)):
                    return (False, None)
                return (True, str(value))
            
            elif param_type == QueryParamType.BLOB:
                # BLOB should be bytes
                if isinstance(value, bytes):
                    return (True, value)
                return (False, None)
            
            return (False, None)
        
        except (ValueError, TypeError):
            return (False, None)


class SafeQueryBuilder:
    """Type-safe SQL query builder with parameterization"""
    
    def __init__(self):
        """Initialize safe query builder"""
        self.sql_prevention = SQLInjectionPrevention()
        self.params: List[Any] = []
        self.param_types: List[QueryParamType] = []
        self.query_parts: List[str] = []
    
    def select(self, columns: Union[str, List[str]]) -> "SafeQueryBuilder":
        """
        Add SELECT clause
        
        Args:
            columns: Column names to select (or "*" for all)
            
        Returns:
            Self for chaining
        """
        if isinstance(columns, str):
            columns = [c.strip() for c in columns.split(",")]
        
        # Validate all columns
        safe_columns = []
        for col in columns:
            # Allow * for SELECT *
            if col == "*":
                safe_columns.append(col)
            elif not self.sql_prevention.validate_identifier(col):
                raise ValueError(f"Invalid column name: {col}")
            else:
                safe_columns.append(col)
        
        self.query_parts.append(f"SELECT {', '.join(safe_columns)}")
        return self
    
    def from_table(self, table_name: str) -> "SafeQueryBuilder":
        """
        Add FROM clause
        
        Args:
            table_name: Table name
            
        Returns:
            Self for chaining
        """
        if not self.sql_prevention.validate_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        self.query_parts.append(f"FROM {table_name}")
        return self
    
    def where_param(
        self, condition: str, value: Any, param_type: QueryParamType = QueryParamType.STRING
    ) -> "SafeQueryBuilder":
        """
        Add WHERE condition with parameterized value
        
        Args:
            condition: Condition with ? placeholder (e.g., "id = ?")
            value: Parameter value
            param_type: Type of parameter
            
        Returns:
            Self for chaining
        """
        # Validate condition doesn't have dangerous patterns
        if ";" in condition or "--" in condition or "/*" in condition:
            raise ValueError("Dangerous pattern in condition")
        
        # Validate parameter value
        is_valid, sanitized = self.sql_prevention.validate_parameter_value(value, param_type)
        if not is_valid:
            raise ValueError(f"Invalid parameter value for type {param_type}")
        
        # Add to parameters
        self.params.append(sanitized)
        self.param_types.append(param_type)
        
        # Add to query
        if not self.query_parts or "WHERE" not in self.query_parts[-1]:
            self.query_parts.append(f"WHERE {condition}")
        else:
            self.query_parts.append(f"AND {condition}")
        
        return self
    
    def build(self) -> Tuple[str, List[Any]]:
        """
        Build final query with parameters
        
        Returns:
            Tuple of (query_string, parameters)
        """
        query = " ".join(self.query_parts)
        return (query, self.params)


def get_sql_injection_prevention() -> SQLInjectionPrevention:
    """
    Get SQL injection prevention singleton
    
    Returns:
        SQLInjectionPrevention instance
    """
    if not hasattr(get_sql_injection_prevention, "_instance"):
        get_sql_injection_prevention._instance = SQLInjectionPrevention()
    return get_sql_injection_prevention._instance
