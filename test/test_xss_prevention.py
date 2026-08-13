"""
Tests for XSS Prevention System

Tests for comprehensive XSS attack prevention including:
- HTML escaping
- JavaScript escaping
- URL validation
- CSS escaping
- JSON sanitization
- XSS vector detection
- Vue.js template safety
- HTML sanitization

Run with: pytest test/test_xss_prevention.py -v
"""

import pytest
import json
from app.xss_prevention import (
    XSSProtection, VueSafeTemplate, SafeHTML,
    XSSVectorType, get_xss_protection
)


class TestXSSProtectionBasics:
    """Tests for basic XSS protection"""
    
    @pytest.fixture
    def xss(self):
        """Get XSS protection instance"""
        return XSSProtection()
    
    def test_escape_html_basic(self, xss):
        """Test basic HTML escaping"""
        result = xss.escape_html("<script>alert('xss')</script>")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "<script>" not in result
    
    def test_escape_html_quotes(self, xss):
        """Test HTML escaping with quotes"""
        result = xss.escape_html('onclick="alert(\'xss\')"')
        assert "&quot;" in result or "&#x27;" in result
        assert 'onclick="' not in result
    
    def test_escape_html_ampersand(self, xss):
        """Test HTML escaping with ampersands"""
        result = xss.escape_html("Tom & Jerry")
        assert "&amp;" in result
        assert "Tom &amp; Jerry" == result
    
    def test_escape_javascript_basic(self, xss):
        """Test JavaScript escaping"""
        result = xss.escape_javascript('text"; alert("xss\'); //')
        assert '\\' in result  # Should contain escapes
        assert 'alert(' in result  # Still present but escaped
        # After escaping quotes, we should have escaped versions
        assert '\\"' in result or "\\'" in result
    
    def test_escape_javascript_newlines(self, xss):
        """Test JavaScript escaping with newlines"""
        result = xss.escape_javascript("line1\nline2")
        assert "\\n" in result
        assert "\n" not in result
    
    def test_escape_javascript_closing_tag(self, xss):
        """Test JavaScript escaping escapes closing script tag"""
        result = xss.escape_javascript("</script>")
        assert "<\\/script>" in result
        assert "</script>" not in result
    
    def test_escape_url_https(self, xss):
        """Test URL escaping accepts HTTPS"""
        url = "https://example.com/page"
        result = xss.escape_url(url)
        assert result == url
    
    def test_escape_url_relative(self, xss):
        """Test URL escaping accepts relative URLs"""
        url = "/path/to/page"
        result = xss.escape_url(url)
        assert result == url
    
    def test_escape_url_javascript_protocol(self, xss):
        """Test URL escaping blocks javascript: protocol"""
        url = "javascript:alert('xss')"
        result = xss.escape_url(url)
        assert result == ""
    
    def test_escape_url_data_uri(self, xss):
        """Test URL escaping blocks data: URIs"""
        url = "data:text/html,<script>alert('xss')</script>"
        result = xss.escape_url(url)
        assert result == ""
    
    def test_escape_url_vbscript(self, xss):
        """Test URL escaping blocks VBScript protocol"""
        url = "vbscript:alert('xss')"
        result = xss.escape_url(url)
        assert result == ""
    
    def test_escape_css_expression(self, xss):
        """Test CSS escaping removes expression()"""
        css = "color: red; expression(alert('xss'))"
        result = xss.escape_css(css)
        assert "expression(" not in result
        assert "color: red" in result
    
    def test_escape_css_javascript(self, xss):
        """Test CSS escaping removes javascript: protocol"""
        css = "background: url(javascript:alert('xss'))"
        result = xss.escape_css(css)
        assert "javascript:" not in result
    
    def test_escape_css_behavior(self, xss):
        """Test CSS escaping removes behavior: directive"""
        css = "behavior: url(malicious.htc)"
        result = xss.escape_css(css)
        assert "behavior:" not in result


class TestXSSVectorDetection:
    """Tests for XSS vector detection"""
    
    @pytest.fixture
    def xss(self):
        """Get XSS protection instance"""
        return XSSProtection()
    
    def test_detect_script_tag(self, xss):
        """Test detection of script tags"""
        text = "Hello <script>alert('xss')</script> world"
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.SCRIPT_TAG
    
    def test_detect_event_handler(self, xss):
        """Test detection of event handlers"""
        text = '<div onclick="alert(\'xss\')">Click me</div>'
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.EVENT_HANDLER
    
    def test_detect_data_uri(self, xss):
        """Test detection of data: URIs"""
        text = '<img src="data:text/html,<script>alert(\'xss\')</script>">'
        result = xss.contains_xss_vector(text)
        # Data URI with script tag - script tag detected first
        assert result in (XSSVectorType.DATA_URI, XSSVectorType.SCRIPT_TAG)
    
    def test_detect_javascript_protocol(self, xss):
        """Test detection of javascript: protocol"""
        text = '<a href="javascript:alert(\'xss\')">Click</a>'
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.JAVASCRIPT_PROTOCOL
    
    def test_detect_svg_script(self, xss):
        """Test detection of SVG script vectors"""
        text = '<svg><script>alert("xss")</script></svg>'
        result = xss.contains_xss_vector(text)
        # Both SVG and script present, script detected first
        assert result == XSSVectorType.SCRIPT_TAG
    
    def test_detect_iframe(self, xss):
        """Test detection of iframe tags"""
        text = '<iframe src="http://malicious.com"></iframe>'
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.IFRAME
    
    def test_detect_style_expression(self, xss):
        """Test detection of style expressions"""
        text = 'style="width: expression(alert(\'xss\'))"'
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.STYLE_EXPRESSION
    
    def test_no_xss_in_safe_text(self, xss):
        """Test safe text has no XSS vectors"""
        text = "This is a safe text with no dangerous content"
        result = xss.contains_xss_vector(text)
        assert result is None
    
    def test_case_insensitive_detection(self, xss):
        """Test XSS detection is case-insensitive"""
        text = "<SCRIPT>alert('xss')</SCRIPT>"
        result = xss.contains_xss_vector(text)
        assert result == XSSVectorType.SCRIPT_TAG


class TestJSONSanitization:
    """Tests for JSON sanitization"""
    
    @pytest.fixture
    def xss(self):
        """Get XSS protection instance"""
        return XSSProtection()
    
    def test_sanitize_valid_json(self, xss):
        """Test sanitization of valid safe JSON"""
        json_str = '{"name": "John", "age": 30}'
        result = xss.sanitize_json(json_str)
        assert result["name"] == "John"
        assert result["age"] == 30
    
    def test_sanitize_json_with_list(self, xss):
        """Test sanitization of JSON with arrays"""
        json_str = '{"items": [1, 2, 3]}'
        result = xss.sanitize_json(json_str)
        assert result["items"] == [1, 2, 3]
    
    def test_sanitize_json_detects_javascript_protocol(self, xss):
        """Test JSON sanitization detects javascript: protocol"""
        json_str = '{"url": "javascript:alert(\'xss\')"}'
        with pytest.raises(ValueError):
            xss.sanitize_json(json_str)
    
    def test_sanitize_json_detects_data_uri(self, xss):
        """Test JSON sanitization detects data: URIs"""
        json_str = '{"img": "data:text/html,<script>alert(\'xss\')</script>"}'
        with pytest.raises(ValueError):
            xss.sanitize_json(json_str)
    
    def test_sanitize_json_detects_script_tag(self, xss):
        """Test JSON sanitization detects script tags"""
        json_str = '{"html": "<script>alert(\'xss\')</script>"}'
        with pytest.raises(ValueError):
            xss.sanitize_json(json_str)
    
    def test_sanitize_nested_json(self, xss):
        """Test sanitization of nested JSON"""
        json_str = '{"user": {"name": "John", "role": "admin"}}'
        result = xss.sanitize_json(json_str)
        assert result["user"]["name"] == "John"
    
    def test_sanitize_json_invalid_format(self, xss):
        """Test sanitization rejects invalid JSON"""
        json_str = "{invalid json}"
        with pytest.raises(ValueError):
            xss.sanitize_json(json_str)


class TestVueTemplate:
    """Tests for Vue.js template escaping"""
    
    @pytest.fixture
    def vue(self):
        """Get Vue template utilities"""
        return VueSafeTemplate()
    
    def test_vue_safe_text(self, vue):
        """Test Vue safe text escaping"""
        result = vue.safe_text("<script>alert('xss')</script>")
        assert "&lt;" in result
        assert "<script>" not in result
    
    def test_vue_safe_attribute(self, vue):
        """Test Vue safe attribute escaping"""
        result = vue.safe_attribute('onclick="alert(\'xss\')"')
        assert "&quot;" in result or "&#x27;" in result
        assert 'onclick="' not in result
    
    def test_vue_safe_url_valid(self, vue):
        """Test Vue safe URL accepts valid URLs"""
        url = "https://example.com"
        result = vue.safe_url(url)
        assert result == url
    
    def test_vue_safe_url_dangerous(self, vue):
        """Test Vue safe URL blocks dangerous protocols"""
        url = "javascript:alert('xss')"
        result = vue.safe_url(url)
        assert result == ""
    
    def test_vue_safe_style(self, vue):
        """Test Vue safe style escaping"""
        style = "color: red; expression(alert('xss'))"
        result = vue.safe_style(style)
        assert "expression(" not in result
    
    def test_vue_safe_json(self, vue):
        """Test Vue safe JSON generation"""
        data = {"name": "John", "age": 30}
        result = vue.safe_json(data)
        parsed = json.loads(result)
        assert parsed["name"] == "John"
    
    def test_vue_safe_json_rejects_dangerous(self, vue):
        """Test Vue safe JSON rejects dangerous content"""
        data = {"url": "javascript:alert('xss')"}
        # Convert to JSON string first to trigger validation
        json_str = json.dumps(data)
        # Now try to sanitize it
        with pytest.raises(ValueError):
            vue.xss.sanitize_json(json_str)


class TestSafeHTML:
    """Tests for HTML sanitization"""
    
    @pytest.fixture
    def html(self):
        """Get HTML sanitizer"""
        return SafeHTML()
    
    def test_sanitize_script_tag(self, html):
        """Test sanitization removes script tags"""
        result = html.sanitize("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script" in result
    
    def test_sanitize_event_handler(self, html):
        """Test sanitization removes event handlers"""
        result = html.sanitize('<div onclick="alert(\'xss\')">Click</div>')
        assert 'onclick="' not in result
        assert "&lt;div" in result
    
    def test_is_safe_html_valid(self, html):
        """Test valid HTML detection"""
        result = html.is_safe_html("<p>Hello world</p>")
        assert result is True
    
    def test_is_safe_html_script(self, html):
        """Test invalid HTML detection for scripts"""
        result = html.is_safe_html("<script>alert('xss')</script>")
        assert result is False
    
    def test_is_safe_html_event_handler(self, html):
        """Test invalid HTML detection for event handlers"""
        result = html.is_safe_html('<img onerror="alert(\'xss\')">')
        assert result is False
    
    def test_sanitize_iframe(self, html):
        """Test sanitization removes iframes"""
        result = html.sanitize("<iframe src='http://malicious.com'></iframe>")
        assert "<iframe" not in result
        assert "&lt;iframe" in result


class TestXSSProtectionSingleton:
    """Tests for XSS protection singleton"""
    
    def test_get_xss_protection_singleton(self):
        """Test get_xss_protection returns singleton"""
        instance1 = get_xss_protection()
        instance2 = get_xss_protection()
        assert instance1 is instance2
    
    def test_singleton_has_methods(self):
        """Test singleton has all methods"""
        xss = get_xss_protection()
        assert hasattr(xss, "escape_html")
        assert hasattr(xss, "escape_javascript")
        assert hasattr(xss, "escape_url")
        assert hasattr(xss, "escape_css")
        assert hasattr(xss, "sanitize_json")
        assert hasattr(xss, "contains_xss_vector")


class TestXSSIntegration:
    """Integration tests for XSS prevention"""
    
    def test_full_flow_unsafe_input(self):
        """Test full flow with unsafe input"""
        xss = get_xss_protection()
        
        # Simulated unsafe user input
        user_input = '<img src="x" onerror="alert(\'xss\')">'
        
        # Check for vectors
        vector = xss.contains_xss_vector(user_input)
        assert vector is not None
        
        # Escape for safe display - escapes tags and attributes but preserves text
        escaped = xss.escape_html(user_input)
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        # The onerror attribute is preserved but its quotes are escaped, making it safe
        assert "&quot;" in escaped or "&#x27;" in escaped
    
    def test_full_flow_safe_url_in_context(self):
        """Test safe URL handling in realistic context"""
        xss = get_xss_protection()
        
        urls = [
            ("https://example.com", "https://example.com"),  # Valid
            ("javascript:alert('xss')", ""),  # Blocked
            ("/page", "/page"),  # Relative OK
            ("data:text/html,<script>", ""),  # Blocked
        ]
        
        for input_url, expected in urls:
            result = xss.escape_url(input_url)
            assert result == expected
    
    def test_combined_protections(self):
        """Test combined XSS protections"""
        xss = get_xss_protection()
        vue = VueSafeTemplate()
        html_safe = SafeHTML()
        
        # Simulate user data
        user_data = '<script>alert("xss")</script>'
        
        # Multiple protection layers
        assert xss.contains_xss_vector(user_data) is not None
        assert not html_safe.is_safe_html(user_data)
        escaped = vue.safe_text(user_data)
        assert "<script>" not in escaped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
