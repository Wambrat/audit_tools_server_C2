"""
CORS (Cross-Origin Resource Sharing) Refinement Security

Provides enhanced CORS security including:
- Origin whitelisting with pattern matching
- Credential-safe CORS configuration
- Allowed methods and headers management
- Preflight cache configuration
- CORS violation detection
- Request validation

Key Classes:
- CORSConfig: Core CORS configuration handler
- CORSValidator: CORS request validation
- OriginMatcher: Origin pattern matching and validation
"""

from typing import List, Optional, Set, Dict, Tuple
from enum import Enum
import re
from urllib.parse import urlparse


class CORSMethod(Enum):
    """HTTP methods allowed by CORS"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class OriginPattern(Enum):
    """CORS origin pattern types"""
    EXACT = "exact"          # Exact origin match
    SUBDOMAIN = "subdomain"  # Allow subdomains of a domain
    WILDCARD = "wildcard"    # Allow any origin (security risk)
    REGEX = "regex"          # Regex pattern matching


class CORSConfig:
    """Core CORS configuration and validation"""
    
    # Standard safe HTTP headers
    SAFE_REQUEST_HEADERS = {
        "accept", "accept-language", "content-language",
        "content-type", "dpr", "downlink", "save-data",
        "viewport-width", "width"
    }
    
    # Safe response headers to expose
    SAFE_RESPONSE_HEADERS = {
        "cache-control", "content-language", "content-length",
        "content-type", "expires", "last-modified", "pragma"
    }
    
    # Dangerous headers that should not be allowed in CORS
    DANGEROUS_HEADERS = {
        "authorization", "cookie", "set-cookie",
        "x-csrf-token", "x-access-token",
        "x-api-key", "x-secret-key"
    }
    
    def __init__(self):
        """Initialize CORS configuration"""
        self.allowed_origins: Dict[str, OriginPattern] = {}
        self.allowed_methods: Set[CORSMethod] = {
            CORSMethod.GET, CORSMethod.HEAD, CORSMethod.OPTIONS
        }
        self.allowed_headers: Set[str] = set(self.SAFE_REQUEST_HEADERS)
        self.exposed_headers: Set[str] = set(self.SAFE_RESPONSE_HEADERS)
        self.max_age: int = 3600  # 1 hour default
        self.allow_credentials: bool = False
    
    def add_allowed_origin(self, origin: str, pattern_type: OriginPattern = OriginPattern.EXACT) -> bool:
        """
        Add allowed origin
        
        Args:
            origin: Origin to allow (e.g., "https://example.com")
            pattern_type: Type of origin pattern
            
        Returns:
            True if added successfully
        """
        if not self._validate_origin_format(origin):
            return False
        
        if pattern_type == OriginPattern.WILDCARD and self.allow_credentials:
            # Cannot use wildcard if credentials are allowed (security risk)
            return False
        
        self.allowed_origins[origin] = pattern_type
        return True
    
    def add_allowed_method(self, method: CORSMethod) -> bool:
        """
        Add allowed HTTP method
        
        Args:
            method: HTTP method to allow
            
        Returns:
            True if added successfully
        """
        self.allowed_methods.add(method)
        return True
    
    def add_allowed_header(self, header: str) -> bool:
        """
        Add allowed request header
        
        Args:
            header: Header name to allow
            
        Returns:
            False if header is dangerous
        """
        header_lower = header.lower()
        
        # Prevent dangerous headers
        if header_lower in self.DANGEROUS_HEADERS:
            return False
        
        self.allowed_headers.add(header_lower)
        return True
    
    def add_exposed_header(self, header: str) -> bool:
        """
        Add exposed response header
        
        Args:
            header: Header name to expose
            
        Returns:
            False if header is dangerous
        """
        header_lower = header.lower()
        
        # Prevent dangerous headers
        if header_lower in self.DANGEROUS_HEADERS:
            return False
        
        self.exposed_headers.add(header_lower)
        return True
    
    def set_credentials_allowed(self, allow: bool) -> bool:
        """
        Set whether credentials are allowed
        
        Args:
            allow: Whether to allow credentials
            
        Returns:
            False if allowing credentials with wildcard origin
        """
        if allow and "*" in self.allowed_origins:
            # Cannot allow credentials with wildcard
            return False
        
        self.allow_credentials = allow
        return True
    
    def set_max_age(self, seconds: int) -> bool:
        """
        Set preflight cache max age
        
        Args:
            seconds: Cache duration in seconds
            
        Returns:
            True if valid, False otherwise
        """
        # Reasonable limits: 1 hour to 7 days
        if seconds < 0 or seconds > (7 * 24 * 3600):
            return False
        
        self.max_age = seconds
        return True
    
    def _validate_origin_format(self, origin: str) -> bool:
        """
        Validate origin format
        
        Args:
            origin: Origin to validate
            
        Returns:
            True if valid format
        """
        if origin == "*":
            # Wildcard is technically valid but insecure
            return True
        
        # Allow domain-only patterns (for subdomain matching)
        # These don't need scheme/netloc validation
        if re.match(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$", origin.lower()):
            return True
        
        try:
            parsed = urlparse(origin)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only http and https allowed
            if parsed.scheme not in ("http", "https"):
                return False
            
            # Must not have path, query, or fragment
            if parsed.path or parsed.query or parsed.fragment:
                return False
            
            return True
        
        except Exception:
            return False


class OriginMatcher:
    """Origin pattern matching and validation"""
    
    def __init__(self):
        """Initialize origin matcher"""
        self.origin_cache: Dict[Tuple[str, str, OriginPattern], bool] = {}
    
    def matches_pattern(
        self, origin: str, pattern: str, pattern_type: OriginPattern
    ) -> bool:
        """
        Check if origin matches pattern
        
        Args:
            origin: Origin to check (e.g., "https://app.example.com")
            pattern: Pattern to match against (e.g., "example.com")
            pattern_type: Type of pattern matching
            
        Returns:
            True if origin matches pattern
        """
        # Check cache
        cache_key = (origin, pattern, pattern_type)
        if cache_key in self.origin_cache:
            return self.origin_cache[cache_key]
        
        result = False
        
        if pattern_type == OriginPattern.EXACT:
            result = origin == pattern
        
        elif pattern_type == OriginPattern.SUBDOMAIN:
            # Allow subdomains of pattern domain
            result = self._match_subdomain(origin, pattern)
        
        elif pattern_type == OriginPattern.WILDCARD:
            # Wildcard matches any origin (risky)
            result = pattern == "*"
        
        elif pattern_type == OriginPattern.REGEX:
            # Regex pattern matching
            result = self._match_regex(origin, pattern)
        
        # Cache result
        self.origin_cache[cache_key] = result
        return result
    
    def _match_subdomain(self, origin: str, domain_pattern: str) -> bool:
        """
        Check if origin is from domain or subdomain
        
        Args:
            origin: Full origin URL
            domain_pattern: Domain pattern (e.g., "example.com")
            
        Returns:
            True if origin matches subdomain pattern
        """
        try:
            parsed = urlparse(origin)
            origin_host = parsed.netloc.lower()
            domain_lower = domain_pattern.lower()
            
            # Exact match
            if origin_host == domain_lower:
                return True
            
            # Subdomain match (must end with .domain)
            if origin_host.endswith(f".{domain_lower}"):
                # Verify it's a valid subdomain (no extra dots at start)
                return not origin_host.startswith(".")
            
            return False
        
        except Exception:
            return False
    
    def _match_regex(self, origin: str, pattern: str) -> bool:
        """
        Check if origin matches regex pattern
        
        Args:
            origin: Origin to check
            pattern: Regex pattern
            
        Returns:
            True if origin matches pattern
        """
        try:
            # Compile pattern (cache could be added for performance)
            compiled = re.compile(f"^{pattern}$", re.IGNORECASE)
            return bool(compiled.match(origin))
        
        except Exception:
            return False
    
    def clear_cache(self):
        """Clear origin matching cache"""
        self.origin_cache.clear()


class CORSValidator:
    """Validates CORS requests"""
    
    def __init__(self, config: CORSConfig):
        """
        Initialize CORS validator
        
        Args:
            config: CORS configuration
        """
        self.config = config
        self.matcher = OriginMatcher()
    
    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed by configuration
        
        Args:
            origin: Origin to validate
            
        Returns:
            True if origin is allowed
        """
        if not origin:
            return False
        
        for pattern, pattern_type in self.config.allowed_origins.items():
            if self.matcher.matches_pattern(origin, pattern, pattern_type):
                return True
        
        return False
    
    def validate_preflight_request(
        self, origin: str, method: str, request_headers: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate preflight (OPTIONS) request
        
        Args:
            origin: Request origin
            method: Requested method (from Access-Control-Request-Method)
            request_headers: Requested headers (from Access-Control-Request-Headers)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check origin
        if not self.is_origin_allowed(origin):
            return (False, f"Origin not allowed: {origin}")
        
        # Check method
        try:
            cors_method = CORSMethod[method.upper()]
            if cors_method not in self.config.allowed_methods:
                return (False, f"Method not allowed: {method}")
        
        except KeyError:
            return (False, f"Invalid method: {method}")
        
        # Check headers
        for header in request_headers:
            header_lower = header.lower()
            if header_lower not in self.config.allowed_headers:
                return (False, f"Header not allowed: {header}")
        
        return (True, None)
    
    def validate_actual_request(
        self, origin: str, method: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate actual CORS request
        
        Args:
            origin: Request origin
            method: Request method
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check origin
        if not self.is_origin_allowed(origin):
            return (False, f"Origin not allowed: {origin}")
        
        # Check method
        try:
            cors_method = CORSMethod[method.upper()]
            if cors_method not in self.config.allowed_methods:
                return (False, f"Method not allowed: {method}")
        
        except KeyError:
            return (False, f"Invalid method: {method}")
        
        return (True, None)
    
    def get_cors_headers(self, origin: str) -> Dict[str, str]:
        """
        Get CORS response headers for origin
        
        Args:
            origin: Request origin
            
        Returns:
            Dictionary of CORS response headers
        """
        headers = {}
        
        if not self.is_origin_allowed(origin):
            return headers
        
        headers["Access-Control-Allow-Origin"] = origin if origin != "*" else "*"
        headers["Access-Control-Allow-Methods"] = ", ".join(
            m.value for m in self.config.allowed_methods
        )
        headers["Access-Control-Allow-Headers"] = ", ".join(
            sorted(self.config.allowed_headers)
        )
        headers["Access-Control-Expose-Headers"] = ", ".join(
            sorted(self.config.exposed_headers)
        )
        headers["Access-Control-Max-Age"] = str(self.config.max_age)
        
        if self.config.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers


def get_default_cors_config() -> CORSConfig:
    """
    Get default secure CORS configuration
    
    Returns:
        CORSConfig with secure defaults
    """
    config = CORSConfig()
    
    # Default: only allow same origin (local)
    config.add_allowed_origin("http://localhost", OriginPattern.EXACT)
    config.add_allowed_origin("http://localhost:3000", OriginPattern.EXACT)
    
    # Default methods: GET, HEAD, OPTIONS (no write operations without explicit config)
    # DELETE and PUT require explicit configuration
    
    return config
