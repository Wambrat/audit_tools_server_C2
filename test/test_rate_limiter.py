"""
Tests unitaires pour app/rate_limiter.py
Teste le système de rate limiting avec sliding window
"""
import pytest
from datetime import datetime, timedelta
from time import sleep
from app.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests pour la classe RateLimiter"""
    
    def test_is_allowed_first_request(self, rate_limiter):
        """Test: Première requête doit être acceptée"""
        allowed, made, remaining = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="beacon",
            max_requests=5,
            window_seconds=60
        )
        
        assert allowed is True
        assert made == 1
        assert remaining == 4  # 5 max - 1 made
    
    def test_is_allowed_multiple_requests(self, rate_limiter):
        """Test: Plusieurs requêtes dans la limite"""
        for i in range(3):
            allowed, made, remaining = rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
            assert allowed is True
            assert made == i + 1
            # After the i-th request (0-indexed), made = i+1, remaining = 5-(i+1) = 4-i
            expected_remaining = 5 - (i + 1)
            assert remaining == expected_remaining, f"Request {i+1}: expected remaining={expected_remaining}, got {remaining}"
    
    def test_rate_limit_exceeded(self, rate_limiter):
        """Test: Rejet quand le limit est atteint"""
        # Faire 5 requêtes (le limit)
        for _ in range(5):
            allowed, _, _ = rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
            assert allowed is True
        
        # 6e requête doit être rejetée
        allowed, made, remaining = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="beacon",
            max_requests=5,
            window_seconds=60
        )
        
        assert allowed is False
        assert made == 5
        assert remaining == 0
    
    def test_different_agents_independent(self, rate_limiter):
        """Test: Chaque agent a son propre limit"""
        # Agent 1 fait 5 requêtes
        for _ in range(5):
            allowed, _, _ = rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
            assert allowed is True
        
        # Agent 2 peut toujours faire une requête
        allowed, made, _ = rate_limiter.is_allowed(
            agent_id="agent-2",
            endpoint="beacon",
            max_requests=5,
            window_seconds=60
        )
        
        assert allowed is True
        assert made == 1
    
    def test_different_endpoints_independent(self, rate_limiter):
        """Test: Chaque endpoint a son propre limit par agent"""
        # Agent 1 fait 5 requêtes sur 'beacon'
        for _ in range(5):
            allowed, _, _ = rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
            assert allowed is True
        
        # Agent 1 peut faire 5 requêtes sur 'results'
        allowed, made, _ = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="results",
            max_requests=5,
            window_seconds=60
        )
        
        assert allowed is True
        assert made == 1
    
    def test_window_expires(self, rate_limiter):
        """Test: Les anciennes requêtes sortent de la fenêtre"""
        # Faire 5 requêtes
        for _ in range(5):
            rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=1  # 1 seconde window
            )
        
        # 6e requête rejetée
        allowed, _, _ = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="beacon",
            max_requests=5,
            window_seconds=1
        )
        assert allowed is False
        
        # Attendre que la fenêtre expire
        sleep(1.1)
        
        # Maintenant ça doit être accepté
        allowed, made, _ = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="beacon",
            max_requests=5,
            window_seconds=1
        )
        assert allowed is True
        assert made == 1  # Compteur remis à zéro
    
    def test_get_stats(self, rate_limiter):
        """Test: Récupérer les stats d'un agent"""
        # Faire 3 requêtes
        for _ in range(3):
            rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=10,
                window_seconds=60
            )
        
        stats = rate_limiter.get_stats("agent-1", "beacon")
        
        assert stats["agent_id"] == "agent-1"
        assert stats["endpoint"] == "beacon"
        assert stats["total_requests"] == 3
        assert stats["last_request"] is not None
        assert stats["requests_in_last_hour"] == 3
    
    def test_reset_agent_endpoint(self, rate_limiter):
        """Test: Réinitialiser le rate limit d'un agent"""
        # Faire 5 requêtes
        for _ in range(5):
            rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
        
        # Réinitialiser
        rate_limiter.reset_agent(agent_id="agent-1", endpoint="beacon")
        
        # Les stats doivent être remis à zéro
        stats = rate_limiter.get_stats("agent-1", "beacon")
        assert stats["total_requests"] == 0
        assert stats["last_request"] is None
    
    def test_zero_requests_remaining(self, rate_limiter):
        """Test: Vérifier que remaining = 0 quand limit atteint"""
        for _ in range(5):
            rate_limiter.is_allowed(
                agent_id="agent-1",
                endpoint="beacon",
                max_requests=5,
                window_seconds=60
            )
        
        _, _, remaining = rate_limiter.is_allowed(
            agent_id="agent-1",
            endpoint="beacon",
            max_requests=5,
            window_seconds=60
        )
        
        assert remaining == 0
