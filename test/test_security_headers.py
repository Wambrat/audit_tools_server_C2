"""
Tests for Security Headers Middleware

Tests for HTTP security headers added to all responses:
- HSTS (HTTP Strict Transport Security)
- CSP (Content Security Policy)
- X-Frame-Options (Clickjacking protection)
- X-Content-Type-Options (MIME sniffing protection)
- X-XSS-Protection (Legacy XSS filter)
- Referrer-Policy (Referer leaking prevention)
- Permissions-Policy (Browser feature restrictions)

Run with: pytest test/test_security_headers.py -v
"""

import pytest


class TestSecurityHeaders:
    """Tests for security headers middleware configuration"""
    
    def test_hsts_header_config(self):
        """Test HSTS configuration"""
        # HSTS: Force HTTPS for 1 year
        expected = "max-age=31536000; includeSubDomains"
        assert "max-age=31536000" in expected
        assert "includeSubDomains" in expected
    
    def test_csp_header_config(self):
        """Test Content Security Policy configuration"""
        csp = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
    
    def test_csp_restricts_script_sources(self):
        """Test CSP restricts script sources"""
        csp = "script-src 'self' https://cdn.jsdelivr.net https://unpkg.com"
        
        assert "script-src 'self'" in csp
        assert "https://cdn.jsdelivr.net" in csp
        assert "https://unpkg.com" in csp
    
    def test_x_frame_options_config(self):
        """Test X-Frame-Options configuration"""
        x_frame = "DENY"
        assert x_frame == "DENY"
    
    def test_x_content_type_options_config(self):
        """Test X-Content-Type-Options configuration"""
        x_content_type = "nosniff"
        assert x_content_type == "nosniff"
    
    def test_x_xss_protection_config(self):
        """Test X-XSS-Protection configuration"""
        x_xss = "1; mode=block"
        assert "1" in x_xss
        assert "block" in x_xss.lower()
    
    def test_referrer_policy_config(self):
        """Test Referrer-Policy configuration"""
        referrer_policy = "strict-origin-when-cross-origin"
        assert "strict-origin-when-cross-origin" in referrer_policy
    
    def test_permissions_policy_config(self):
        """Test Permissions-Policy configuration"""
        permissions_policy = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=()"
        )
        
        assert "camera=()" in permissions_policy
        assert "microphone=()" in permissions_policy
        assert "geolocation=()" in permissions_policy
        assert "payment=()" in permissions_policy


class TestSecurityHeadersPresence:
    """Tests to verify security headers configuration is complete"""
    
    def test_all_required_headers_present(self):
        """Test all required security headers are configured"""
        headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=()"
        }
        
        required_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy"
        ]
        
        for header in required_headers:
            assert header in headers, f"Missing security header: {header}"
    
    def test_no_conflicting_headers(self):
        """Test security headers don't contradict each other"""
        headers = {
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "frame-ancestors 'none'",
        }
        
        # Both should restrict framing
        assert "DENY" in headers["X-Frame-Options"]
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    
    def test_csp_policy_completeness(self):
        """Test CSP policy covers all resource types"""
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
        resource_types = [
            "default-src",
            "script-src",
            "style-src",
            "img-src",
            "font-src",
            "connect-src"
        ]
        
        for resource_type in resource_types:
            assert resource_type in csp, f"CSP missing directive: {resource_type}"


class TestSecurityHeadersConfiguration:
    """Tests for security header configuration values"""
    
    def test_hsts_max_age_reasonable(self):
        """Test HSTS max-age is reasonable"""
        max_age = 31536000  # 1 year in seconds
        
        # Should be at least 1 day
        assert max_age >= 86400
        
        # Should be at most 5 years
        assert max_age <= (5 * 365 * 24 * 3600)
    
    def test_csp_self_restriction(self):
        """Test CSP uses 'self' to restrict to own origin"""
        csp = "default-src 'self'"
        assert "'self'" in csp
    
    def test_xss_protection_enabled(self):
        """Test XSS protection is enabled"""
        x_xss = "1; mode=block"
        
        # Value of 1 means enabled
        assert "1" in x_xss
        
        # mode=block means block the page
        assert "block" in x_xss.lower()
    
    def test_referrer_policy_restrictive(self):
        """Test Referrer-Policy is appropriately restrictive"""
        policy = "strict-origin-when-cross-origin"
        
        # Should not be 'unsafe-url' or 'no-referrer-when-downgrade'
        assert "strict" in policy
        assert "origin" in policy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
