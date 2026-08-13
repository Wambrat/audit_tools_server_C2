"""
Tests for CORS Security Refinement

Tests for CORS security configuration and validation including:
- Origin whitelisting
- Method validation
- Header validation
- Credentials safety
- Preflight request handling
- Origin pattern matching

Run with: pytest test/test_cors_security.py -v
"""

import pytest
from app.cors_security import (
    CORSConfig, CORSValidator, OriginMatcher,
    CORSMethod, OriginPattern, get_default_cors_config
)


class TestCORSConfiguration:
    """Tests for CORS configuration"""
    
    @pytest.fixture
    def cors_config(self):
        """Get CORS configuration"""
        return CORSConfig()
    
    def test_add_allowed_origin_exact(self, cors_config):
        """Test adding exact origin"""
        result = cors_config.add_allowed_origin(
            "https://example.com", OriginPattern.EXACT
        )
        assert result is True
        assert "https://example.com" in cors_config.allowed_origins
    
    def test_add_allowed_origin_subdomain(self, cors_config):
        """Test adding subdomain pattern"""
        result = cors_config.add_allowed_origin(
            "example.com", OriginPattern.SUBDOMAIN
        )
        assert result is True
    
    def test_add_invalid_origin_format(self, cors_config):
        """Test adding invalid origin format"""
        result = cors_config.add_allowed_origin(
            "invalid origin", OriginPattern.EXACT
        )
        assert result is False
    
    def test_wildcard_with_credentials_forbidden(self, cors_config):
        """Test wildcard origin forbidden with credentials"""
        cors_config.allow_credentials = True
        result = cors_config.add_allowed_origin("*", OriginPattern.WILDCARD)
        assert result is False
    
    def test_add_allowed_method(self, cors_config):
        """Test adding allowed method"""
        result = cors_config.add_allowed_method(CORSMethod.POST)
        assert result is True
        assert CORSMethod.POST in cors_config.allowed_methods
    
    def test_add_allowed_header_safe(self, cors_config):
        """Test adding safe request header"""
        result = cors_config.add_allowed_header("X-Custom-Header")
        assert result is True
        assert "x-custom-header" in cors_config.allowed_headers
    
    def test_add_dangerous_header_blocked(self, cors_config):
        """Test dangerous header is blocked"""
        result = cors_config.add_allowed_header("Authorization")
        assert result is False
    
    def test_add_dangerous_header_cookie(self, cors_config):
        """Test Cookie header is blocked"""
        result = cors_config.add_allowed_header("Cookie")
        assert result is False
    
    def test_add_exposed_header_safe(self, cors_config):
        """Test adding safe exposed header"""
        result = cors_config.add_exposed_header("X-Custom-Response")
        assert result is True
        assert "x-custom-response" in cors_config.exposed_headers
    
    def test_add_exposed_header_dangerous(self, cors_config):
        """Test dangerous exposed header is blocked"""
        result = cors_config.add_exposed_header("X-API-Key")
        assert result is False
    
    def test_set_credentials_allowed(self, cors_config):
        """Test setting credentials allowed"""
        cors_config.add_allowed_origin("https://example.com", OriginPattern.EXACT)
        result = cors_config.set_credentials_allowed(True)
        assert result is True
        assert cors_config.allow_credentials is True
    
    def test_set_credentials_with_wildcard_fails(self, cors_config):
        """Test credentials not allowed with wildcard"""
        cors_config.add_allowed_origin("*", OriginPattern.WILDCARD)
        result = cors_config.set_credentials_allowed(True)
        assert result is False
    
    def test_set_valid_max_age(self, cors_config):
        """Test setting valid max age"""
        result = cors_config.set_max_age(3600)
        assert result is True
        assert cors_config.max_age == 3600
    
    def test_set_negative_max_age(self, cors_config):
        """Test negative max age is invalid"""
        result = cors_config.set_max_age(-1)
        assert result is False
    
    def test_set_max_age_too_large(self, cors_config):
        """Test max age too large is invalid"""
        result = cors_config.set_max_age(10 * 365 * 24 * 3600)  # 10 years
        assert result is False


class TestOriginMatcher:
    """Tests for origin pattern matching"""
    
    @pytest.fixture
    def matcher(self):
        """Get origin matcher"""
        return OriginMatcher()
    
    def test_exact_match_success(self, matcher):
        """Test exact origin matching"""
        result = matcher.matches_pattern(
            "https://example.com",
            "https://example.com",
            OriginPattern.EXACT
        )
        assert result is True
    
    def test_exact_match_failure(self, matcher):
        """Test exact origin matching failure"""
        result = matcher.matches_pattern(
            "https://example.com",
            "https://other.com",
            OriginPattern.EXACT
        )
        assert result is False
    
    def test_subdomain_match_exact(self, matcher):
        """Test subdomain matching - exact domain"""
        result = matcher.matches_pattern(
            "https://example.com",
            "example.com",
            OriginPattern.SUBDOMAIN
        )
        assert result is True
    
    def test_subdomain_match_subdomain(self, matcher):
        """Test subdomain matching - actual subdomain"""
        result = matcher.matches_pattern(
            "https://app.example.com",
            "example.com",
            OriginPattern.SUBDOMAIN
        )
        assert result is True
    
    def test_subdomain_match_deep(self, matcher):
        """Test subdomain matching - deep subdomain"""
        result = matcher.matches_pattern(
            "https://api.v1.example.com",
            "example.com",
            OriginPattern.SUBDOMAIN
        )
        assert result is True
    
    def test_subdomain_no_match_other_domain(self, matcher):
        """Test subdomain matching - different domain"""
        result = matcher.matches_pattern(
            "https://examplecom.net",
            "example.com",
            OriginPattern.SUBDOMAIN
        )
        assert result is False
    
    def test_wildcard_match(self, matcher):
        """Test wildcard pattern matching"""
        result = matcher.matches_pattern(
            "https://any-origin.com",
            "*",
            OriginPattern.WILDCARD
        )
        assert result is True
    
    def test_wildcard_no_match(self, matcher):
        """Test wildcard pattern non-match"""
        result = matcher.matches_pattern(
            "https://any-origin.com",
            "specific.com",
            OriginPattern.WILDCARD
        )
        assert result is False
    
    def test_regex_match_exact(self, matcher):
        """Test regex pattern matching - exact"""
        result = matcher.matches_pattern(
            "https://example.com",
            r"https://example\.com",
            OriginPattern.REGEX
        )
        assert result is True
    
    def test_regex_match_pattern(self, matcher):
        """Test regex pattern matching - pattern"""
        result = matcher.matches_pattern(
            "https://app.example.com",
            r"https://.*\.example\.com",
            OriginPattern.REGEX
        )
        assert result is True
    
    def test_cache_functionality(self, matcher):
        """Test caching improves performance"""
        origin = "https://example.com"
        pattern = "https://example.com"
        
        # First call
        matcher.matches_pattern(origin, pattern, OriginPattern.EXACT)
        assert len(matcher.origin_cache) == 1
        
        # Second call should use cache
        result = matcher.matches_pattern(origin, pattern, OriginPattern.EXACT)
        assert result is True
        assert len(matcher.origin_cache) == 1
    
    def test_clear_cache(self, matcher):
        """Test cache clearing"""
        matcher.matches_pattern("https://example.com", "https://example.com", OriginPattern.EXACT)
        assert len(matcher.origin_cache) > 0
        
        matcher.clear_cache()
        assert len(matcher.origin_cache) == 0


class TestCORSValidator:
    """Tests for CORS request validation"""
    
    @pytest.fixture
    def config_and_validator(self):
        """Get CORS config and validator"""
        config = CORSConfig()
        config.add_allowed_origin("https://app.example.com", OriginPattern.EXACT)
        config.add_allowed_origin("example.com", OriginPattern.SUBDOMAIN)
        config.add_allowed_method(CORSMethod.POST)
        config.add_allowed_method(CORSMethod.PUT)
        validator = CORSValidator(config)
        return config, validator
    
    def test_is_origin_allowed_exact(self, config_and_validator):
        """Test origin allowed - exact match"""
        _, validator = config_and_validator
        result = validator.is_origin_allowed("https://app.example.com")
        assert result is True
    
    def test_is_origin_allowed_subdomain(self, config_and_validator):
        """Test origin allowed - subdomain match"""
        _, validator = config_and_validator
        result = validator.is_origin_allowed("https://api.example.com")
        assert result is True
    
    def test_is_origin_not_allowed(self, config_and_validator):
        """Test origin not allowed"""
        _, validator = config_and_validator
        result = validator.is_origin_allowed("https://malicious.com")
        assert result is False
    
    def test_validate_preflight_success(self, config_and_validator):
        """Test preflight request validation - success"""
        config, validator = config_and_validator
        config.add_allowed_header("X-Custom-Header")
        
        is_valid, error = validator.validate_preflight_request(
            "https://app.example.com",
            "POST",
            ["Content-Type", "X-Custom-Header"]
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_preflight_bad_origin(self, config_and_validator):
        """Test preflight request validation - bad origin"""
        _, validator = config_and_validator
        is_valid, error = validator.validate_preflight_request(
            "https://bad.com",
            "POST",
            []
        )
        assert is_valid is False
        assert "not allowed" in error.lower()
    
    def test_validate_preflight_bad_method(self, config_and_validator):
        """Test preflight request validation - bad method"""
        _, validator = config_and_validator
        is_valid, error = validator.validate_preflight_request(
            "https://app.example.com",
            "DELETE",  # Not in allowed methods
            []
        )
        assert is_valid is False
        assert "not allowed" in error.lower()
    
    def test_validate_preflight_bad_header(self, config_and_validator):
        """Test preflight request validation - unauthorized header"""
        _, validator = config_and_validator
        
        # First add a custom header as allowed
        config, _ = config_and_validator
        config.add_allowed_header("X-Custom-Header")
        
        is_valid, error = validator.validate_preflight_request(
            "https://app.example.com",
            "POST",
            ["X-API-Key"]  # Not allowed header
        )
        assert is_valid is False
        assert "not allowed" in error.lower()
    
    def test_validate_actual_request_success(self, config_and_validator):
        """Test actual request validation - success"""
        _, validator = config_and_validator
        is_valid, error = validator.validate_actual_request(
            "https://app.example.com",
            "POST"
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_actual_request_bad_origin(self, config_and_validator):
        """Test actual request validation - bad origin"""
        _, validator = config_and_validator
        is_valid, error = validator.validate_actual_request(
            "https://bad.com",
            "POST"
        )
        assert is_valid is False
    
    def test_validate_actual_request_bad_method(self, config_and_validator):
        """Test actual request validation - bad method"""
        _, validator = config_and_validator
        is_valid, error = validator.validate_actual_request(
            "https://app.example.com",
            "DELETE"  # Not allowed
        )
        assert is_valid is False
    
    def test_get_cors_headers_complete(self, config_and_validator):
        """Test getting complete CORS headers"""
        config, validator = config_and_validator
        config.set_credentials_allowed(False)
        
        headers = validator.get_cors_headers("https://app.example.com")
        
        assert "Access-Control-Allow-Origin" in headers
        assert headers["Access-Control-Allow-Origin"] == "https://app.example.com"
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Max-Age" in headers
    
    def test_get_cors_headers_no_credentials(self, config_and_validator):
        """Test CORS headers without credentials"""
        _, validator = config_and_validator
        headers = validator.get_cors_headers("https://app.example.com")
        
        assert "Access-Control-Allow-Credentials" not in headers
    
    def test_get_cors_headers_with_credentials(self, config_and_validator):
        """Test CORS headers with credentials"""
        config, validator = config_and_validator
        config.set_credentials_allowed(True)
        
        headers = validator.get_cors_headers("https://app.example.com")
        assert headers.get("Access-Control-Allow-Credentials") == "true"
    
    def test_get_cors_headers_bad_origin(self, config_and_validator):
        """Test getting CORS headers for bad origin"""
        _, validator = config_and_validator
        headers = validator.get_cors_headers("https://bad.com")
        
        assert len(headers) == 0


class TestDefaultCORSConfig:
    """Tests for default CORS configuration"""
    
    def test_default_config_secure(self):
        """Test default config is secure"""
        config = get_default_cors_config()
        
        # Should only allow localhost by default
        assert len(config.allowed_origins) == 2
        assert "http://localhost" in config.allowed_origins
        
        # Should not allow credentials by default
        assert config.allow_credentials is False
        
        # Should allow safe methods only
        assert CORSMethod.GET in config.allowed_methods
        assert CORSMethod.HEAD in config.allowed_methods
        assert CORSMethod.OPTIONS in config.allowed_methods
        # DELETE and PUT should not be default
        assert CORSMethod.DELETE not in config.allowed_methods
        assert CORSMethod.PUT not in config.allowed_methods


class TestCORSIntegration:
    """Integration tests for CORS security"""
    
    def test_secure_cors_flow_preflight(self):
        """Test secure CORS flow - preflight"""
        config = CORSConfig()
        config.add_allowed_origin("https://trusted-app.com", OriginPattern.EXACT)
        config.add_allowed_method(CORSMethod.POST)
        config.add_allowed_header("Content-Type")
        
        validator = CORSValidator(config)
        
        # Preflight request
        is_valid, error = validator.validate_preflight_request(
            "https://trusted-app.com",
            "POST",
            ["Content-Type"]
        )
        assert is_valid is True
        
        # Get CORS headers
        headers = validator.get_cors_headers("https://trusted-app.com")
        assert len(headers) > 0
    
    def test_untrusted_origin_rejected(self):
        """Test untrusted origin is rejected"""
        config = CORSConfig()
        config.add_allowed_origin("https://trusted.com", OriginPattern.EXACT)
        
        validator = CORSValidator(config)
        
        # Untrusted origin
        is_valid, _ = validator.validate_actual_request(
            "https://untrusted.com",
            "GET"
        )
        assert is_valid is False
        
        # No headers for untrusted origin
        headers = validator.get_cors_headers("https://untrusted.com")
        assert len(headers) == 0
    
    def test_wildcard_security_implications(self):
        """Test wildcard CORS security implications"""
        config = CORSConfig()
        
        # Wildcard without credentials is acceptable
        result = config.add_allowed_origin("*", OriginPattern.WILDCARD)
        assert result is True
        
        # But cannot enable credentials
        result = config.set_credentials_allowed(True)
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
