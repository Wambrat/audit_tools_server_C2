"""
Tests for SQL Injection Prevention System

Tests for SQL injection attack prevention including:
- Pattern detection (UNION, boolean blind, time-based, etc.)
- SQL keyword detection
- String escaping
- Identifier validation
- Parameterized query building
- Type validation

Run with: pytest test/test_sql_injection_prevention.py -v
"""

import pytest
from app.sql_injection_prevention import (
    SQLInjectionPrevention, SafeQueryBuilder,
    SQLDangerPattern, QueryParamType,
    get_sql_injection_prevention
)


class TestSQLPatternDetection:
    """Tests for SQL injection pattern detection"""
    
    @pytest.fixture
    def sql_prev(self):
        """Get SQL prevention instance"""
        return SQLInjectionPrevention()
    
    def test_detect_union_based_injection(self, sql_prev):
        """Test detection of UNION-based injection"""
        payload = "1' UNION SELECT * FROM users --"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.UNION_BASED
    
    def test_detect_boolean_blind_injection(self, sql_prev):
        """Test detection of boolean blind injection"""
        payload = "1 OR 1=1"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.BOOLEAN_BLIND
    
    def test_detect_time_based_injection(self, sql_prev):
        """Test detection of time-based blind injection"""
        payload = "1 WAITFOR DELAY '00:00:05'"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.TIMED
    
    def test_detect_sleep_injection(self, sql_prev):
        """Test detection of sleep injection"""
        payload = "1' AND SLEEP(5) --"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.TIMED
    
    def test_detect_error_based_injection(self, sql_prev):
        """Test detection of error-based injection"""
        payload = "1' AND EXTRACTVALUE(1, CONCAT(0x7e, database())) --"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.ERROR_BASED
    
    def test_detect_stacked_queries(self, sql_prev):
        """Test detection of stacked queries"""
        payload = "1'; DROP TABLE users; --"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.STACKED_QUERIES
    
    def test_detect_comment_injection(self, sql_prev):
        """Test detection of comment injection"""
        payload = "admin'--"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.COMMENT_INJECTION
    
    def test_detect_mysql_comment(self, sql_prev):
        """Test detection of MySQL comment syntax"""
        payload = "admin' #"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.COMMENT_INJECTION
    
    def test_detect_c_style_comment(self, sql_prev):
        """Test detection of C-style comment"""
        payload = "admin' /* */'"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.COMMENT_INJECTION
    
    def test_detect_string_termination(self, sql_prev):
        """Test detection of string termination with logic"""
        payload = "' OR '1'='1' --"
        result = sql_prev.detect_injection_pattern(payload)
        # Either comment or boolean blind detection is fine
        assert result in (SQLDangerPattern.BOOLEAN_BLIND, SQLDangerPattern.COMMENT_INJECTION)
    
    def test_detect_wildcard_injection(self, sql_prev):
        """Test detection of wildcard injection"""
        payload = "%"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.WILDCARD_INJECTION
    
    def test_safe_input_no_detection(self, sql_prev):
        """Test safe input doesn't trigger detection"""
        payload = "john@example.com"
        result = sql_prev.detect_injection_pattern(payload)
        assert result is None
    
    def test_case_insensitive_detection(self, sql_prev):
        """Test detection is case-insensitive"""
        payload = "1' UnIoN SeLeCt * FROM users --"
        result = sql_prev.detect_injection_pattern(payload)
        assert result == SQLDangerPattern.UNION_BASED


class TestSQLKeywordDetection:
    """Tests for SQL keyword detection"""
    
    @pytest.fixture
    def sql_prev(self):
        """Get SQL prevention instance"""
        return SQLInjectionPrevention()
    
    def test_detect_select_keyword(self, sql_prev):
        """Test detection of SELECT keyword"""
        result = sql_prev.contains_sql_keyword("SELECT * FROM users")
        assert result is True
    
    def test_detect_drop_keyword(self, sql_prev):
        """Test detection of DROP keyword"""
        result = sql_prev.contains_sql_keyword("DROP TABLE users")
        assert result is True
    
    def test_detect_union_keyword(self, sql_prev):
        """Test detection of UNION keyword"""
        result = sql_prev.contains_sql_keyword("UNION SELECT")
        assert result is True
    
    def test_keyword_in_safe_context(self, sql_prev):
        """Test keyword detection in safe context"""
        # "select" in a normal word
        result = sql_prev.contains_sql_keyword("select_user", strict=True)
        assert result is False
    
    def test_safe_input_no_keywords(self, sql_prev):
        """Test safe input has no keywords"""
        result = sql_prev.contains_sql_keyword("john@example.com")
        assert result is False


class TestSQLStringEscaping:
    """Tests for SQL string escaping"""
    
    @pytest.fixture
    def sql_prev(self):
        """Get SQL prevention instance"""
        return SQLInjectionPrevention()
    
    def test_escape_single_quote(self, sql_prev):
        """Test escaping single quotes"""
        result = sql_prev.escape_sql_string("O'Brien")
        assert result == "'O''Brien'"
    
    def test_escape_double_quote(self, sql_prev):
        """Test escaping double quotes"""
        result = sql_prev.escape_sql_string('Say "Hello"', quote_char='"')
        assert result == '"Say ""Hello"""'
    
    def test_escape_backslash(self, sql_prev):
        """Test escaping backslashes"""
        result = sql_prev.escape_sql_string("Path\\to\\file")
        # Should have escaped backslashes
        assert "\\\\" in result or result.count("\\") >= 4
    
    def test_escape_injection_attempt(self, sql_prev):
        """Test escaping injection attempt"""
        payload = "'; DROP TABLE users; --"
        result = sql_prev.escape_sql_string(payload)
        # Should be escaped in quotes
        assert result.startswith("'") and result.endswith("'")
        assert "''; DROP TABLE users; --" in result or "\\'" in result
    
    def test_empty_string_escaping(self, sql_prev):
        """Test escaping empty string"""
        result = sql_prev.escape_sql_string("")
        assert result == "''"


class TestIdentifierValidation:
    """Tests for SQL identifier validation"""
    
    @pytest.fixture
    def sql_prev(self):
        """Get SQL prevention instance"""
        return SQLInjectionPrevention()
    
    def test_valid_table_name(self, sql_prev):
        """Test valid table name"""
        result = sql_prev.validate_identifier("users")
        assert result is True
    
    def test_valid_table_with_underscore(self, sql_prev):
        """Test valid table name with underscore"""
        result = sql_prev.validate_identifier("user_profiles")
        assert result is True
    
    def test_valid_table_with_numbers(self, sql_prev):
        """Test valid table name with numbers"""
        result = sql_prev.validate_identifier("table2024")
        assert result is True
    
    def test_invalid_starts_with_number(self, sql_prev):
        """Test invalid identifier starting with number"""
        result = sql_prev.validate_identifier("2users")
        assert result is False
    
    def test_invalid_with_space(self, sql_prev):
        """Test invalid identifier with space"""
        result = sql_prev.validate_identifier("user table")
        assert result is False
    
    def test_invalid_with_special_char(self, sql_prev):
        """Test invalid identifier with special character"""
        result = sql_prev.validate_identifier("user-table")
        assert result is False
    
    def test_invalid_sql_keyword(self, sql_prev):
        """Test SQL keyword as identifier"""
        result = sql_prev.validate_identifier("select")
        assert result is False
    
    def test_invalid_too_long(self, sql_prev):
        """Test identifier too long"""
        result = sql_prev.validate_identifier("a" * 100)
        assert result is False
    
    def test_empty_identifier(self, sql_prev):
        """Test empty identifier"""
        result = sql_prev.validate_identifier("")
        assert result is False
    
    def test_sanitize_table_name_valid(self, sql_prev):
        """Test sanitize valid table name"""
        result = sql_prev.sanitize_table_name("users")
        assert result == "users"
    
    def test_sanitize_table_name_invalid(self, sql_prev):
        """Test sanitize invalid table name"""
        result = sql_prev.sanitize_table_name("select")
        assert result == ""
    
    def test_sanitize_column_name_valid(self, sql_prev):
        """Test sanitize valid column name"""
        result = sql_prev.sanitize_column_name("user_id")
        assert result == "user_id"
    
    def test_sanitize_column_name_invalid(self, sql_prev):
        """Test sanitize invalid column name"""
        result = sql_prev.sanitize_column_name("user id")
        assert result == ""


class TestParameterValidation:
    """Tests for parameter type validation"""
    
    @pytest.fixture
    def sql_prev(self):
        """Get SQL prevention instance"""
        return SQLInjectionPrevention()
    
    def test_validate_string_param(self, sql_prev):
        """Test string parameter validation"""
        is_valid, value = sql_prev.validate_parameter_value("test", QueryParamType.STRING)
        assert is_valid is True
        assert value == "test"
    
    def test_validate_integer_param(self, sql_prev):
        """Test integer parameter validation"""
        is_valid, value = sql_prev.validate_parameter_value("42", QueryParamType.INTEGER)
        assert is_valid is True
        assert value == 42
    
    def test_validate_integer_invalid(self, sql_prev):
        """Test invalid integer parameter"""
        is_valid, value = sql_prev.validate_parameter_value("not_a_number", QueryParamType.INTEGER)
        assert is_valid is False
    
    def test_validate_float_param(self, sql_prev):
        """Test float parameter validation"""
        is_valid, value = sql_prev.validate_parameter_value("3.14", QueryParamType.FLOAT)
        assert is_valid is True
        assert abs(value - 3.14) < 0.01
    
    def test_validate_boolean_true(self, sql_prev):
        """Test boolean parameter - true"""
        is_valid, value = sql_prev.validate_parameter_value("true", QueryParamType.BOOLEAN)
        assert is_valid is True
        assert value is True
    
    def test_validate_boolean_false(self, sql_prev):
        """Test boolean parameter - false"""
        is_valid, value = sql_prev.validate_parameter_value("false", QueryParamType.BOOLEAN)
        assert is_valid is True
        assert value is False
    
    def test_validate_date_iso8601(self, sql_prev):
        """Test date parameter - ISO 8601"""
        is_valid, value = sql_prev.validate_parameter_value("2024-06-16", QueryParamType.DATE)
        assert is_valid is True
    
    def test_validate_date_invalid(self, sql_prev):
        """Test invalid date parameter"""
        is_valid, value = sql_prev.validate_parameter_value("06/16/2024", QueryParamType.DATE)
        assert is_valid is False
    
    def test_validate_blob_bytes(self, sql_prev):
        """Test BLOB parameter with bytes"""
        is_valid, value = sql_prev.validate_parameter_value(b"binary_data", QueryParamType.BLOB)
        assert is_valid is True


class TestSafeQueryBuilder:
    """Tests for safe query builder"""
    
    def test_build_simple_select(self):
        """Test building simple SELECT query"""
        builder = SafeQueryBuilder()
        query, params = builder.select("id, name").from_table("users").build()
        
        assert "SELECT id, name" in query
        assert "FROM users" in query
        assert params == []
    
    def test_select_with_comma_separated(self):
        """Test SELECT with comma-separated columns"""
        builder = SafeQueryBuilder()
        query, params = builder.select("id, name, email").from_table("users").build()
        
        assert "SELECT id, name, email" in query
    
    def test_where_with_string_parameter(self):
        """Test WHERE clause with string parameter"""
        builder = SafeQueryBuilder()
        query, params = builder.select("*").from_table("users").where_param(
            "email = ?", "john@example.com", QueryParamType.STRING
        ).build()
        
        assert "WHERE email = ?" in query
        assert params == ["john@example.com"]
    
    def test_where_with_integer_parameter(self):
        """Test WHERE clause with integer parameter"""
        builder = SafeQueryBuilder()
        query, params = builder.select("*").from_table("users").where_param(
            "id = ?", 42, QueryParamType.INTEGER
        ).build()
        
        assert "WHERE id = ?" in query
        assert params == [42]
    
    def test_multiple_where_conditions(self):
        """Test multiple WHERE conditions"""
        builder = SafeQueryBuilder()
        query, params = (
            builder
            .select("*")
            .from_table("users")
            .where_param("id = ?", 1, QueryParamType.INTEGER)
            .where_param("name = ?", "John", QueryParamType.STRING)
            .build()
        )
        
        assert "WHERE id = ?" in query
        assert "AND name = ?" in query
        assert params == [1, "John"]
    
    def test_invalid_table_name(self):
        """Test invalid table name raises error"""
        builder = SafeQueryBuilder()
        
        with pytest.raises(ValueError):
            builder.from_table("select")
    
    def test_invalid_column_name(self):
        """Test invalid column name raises error"""
        builder = SafeQueryBuilder()
        
        with pytest.raises(ValueError):
            builder.select("drop")
    
    def test_dangerous_where_condition(self):
        """Test dangerous WHERE condition raises error"""
        builder = SafeQueryBuilder()
        
        with pytest.raises(ValueError):
            builder.select("*").from_table("users").where_param(
                "id = ?; DROP TABLE users", 1, QueryParamType.INTEGER
            )
    
    def test_invalid_parameter_type(self):
        """Test invalid parameter type raises error"""
        builder = SafeQueryBuilder()
        
        with pytest.raises(ValueError):
            builder.select("*").from_table("users").where_param(
                "age = ?", "not_a_number", QueryParamType.INTEGER
            )


class TestSQLInjectionSingleton:
    """Tests for SQL injection prevention singleton"""
    
    def test_singleton_instance(self):
        """Test get_sql_injection_prevention returns singleton"""
        instance1 = get_sql_injection_prevention()
        instance2 = get_sql_injection_prevention()
        assert instance1 is instance2
    
    def test_singleton_has_methods(self):
        """Test singleton has all methods"""
        sql_prev = get_sql_injection_prevention()
        assert hasattr(sql_prev, "detect_injection_pattern")
        assert hasattr(sql_prev, "contains_sql_keyword")
        assert hasattr(sql_prev, "escape_sql_string")
        assert hasattr(sql_prev, "validate_identifier")


class TestSQLInjectionIntegration:
    """Integration tests for SQL injection prevention"""
    
    def test_full_flow_detect_and_prevent(self):
        """Test full flow of injection detection and prevention"""
        sql_prev = get_sql_injection_prevention()
        
        payloads = [
            ("'; DROP TABLE users; --", SQLDangerPattern.STACKED_QUERIES),
            ("1 OR 1=1", SQLDangerPattern.BOOLEAN_BLIND),
            ("1' UNION SELECT * FROM users", SQLDangerPattern.UNION_BASED),
            ("admin'--", SQLDangerPattern.COMMENT_INJECTION),
        ]
        
        for payload, expected_pattern in payloads:
            pattern = sql_prev.detect_injection_pattern(payload)
            assert pattern == expected_pattern
    
    def test_safe_query_builder_prevents_injection(self):
        """Test safe query builder prevents injections"""
        builder = SafeQueryBuilder()
        
        # Try to inject via where_param
        with pytest.raises(ValueError):
            builder.select("*").from_table("users").where_param(
                "id = ?; DROP TABLE users", 1, QueryParamType.INTEGER
            )
    
    def test_parameterized_queries_safe(self):
        """Test parameterized queries are safe"""
        builder = SafeQueryBuilder()
        
        # Even injection attempt in parameter value is safe (not in query structure)
        query, params = (
            builder
            .select("*")
            .from_table("users")
            .where_param("comment = ?", "'; DROP TABLE users; --", QueryParamType.STRING)
            .build()
        )
        
        # Injection in value is safe because it's parameterized
        assert "DROP" not in query
        assert params[0] == "'; DROP TABLE users; --"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
