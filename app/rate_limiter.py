"""
Système de rate limiting pour limiter les requêtes par agent.
Utilise une stratégie sliding window avec timestamps.
"""
from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from .logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter basé sur une sliding window.
    Limite les requêtes par agent et par endpoint.
    """
    
    def __init__(self):
        # Structure: {endpoint: {agent_id: [(timestamp1, timestamp2, ...)]}}
        self.request_history: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
    
    def is_allowed(
        self,
        agent_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Vérifier si l'agent peut faire une requête.
        
        Args:
            agent_id: ID de l'agent
            endpoint: Nom de l'endpoint (ex: "beacon", "results")
            max_requests: Nombre maximum de requêtes
            window_seconds: Fenêtre de temps en secondes
        
        Returns:
            (allowed, requests_made, requests_remaining)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Récupérer l'historique pour cet agent et endpoint
        history = self.request_history[endpoint][agent_id]
        
        # Nettoyer les requêtes en dehors de la fenêtre
        history[:] = [ts for ts in history if ts > window_start]
        
        requests_made = len(history)
        requests_remaining = max(0, max_requests - requests_made)
        
        # Vérifier si le limit est atteint
        if requests_made >= max_requests:
            logger.warning(
                f"Rate limit exceeded: agent_id={agent_id}, endpoint={endpoint}, requests_made={requests_made}, max_requests={max_requests}"
            )
            return False, requests_made, requests_remaining
        
        # Enregistrer la requête
        history.append(now)
        requests_made_after = len(history)
        requests_remaining_after = max(0, max_requests - requests_made_after)
        
        logger.debug(
            f"Request allowed: agent_id={agent_id}, endpoint={endpoint}, requests_made={requests_made_after}, max_requests={max_requests}"
        )
        
        return True, requests_made_after, requests_remaining_after
    
    def get_stats(self, agent_id: str, endpoint: str) -> Dict:
        """Récupérer les stats d'un agent pour un endpoint"""
        history = self.request_history[endpoint][agent_id]
        now = datetime.now()
        
        return {
            "agent_id": agent_id,
            "endpoint": endpoint,
            "total_requests": len(history),
            "last_request": history[-1].isoformat() if history else None,
            "requests_in_last_hour": len([
                ts for ts in history 
                if ts > now - timedelta(hours=1)
            ])
        }
    
    def reset_agent(self, agent_id: str = None, endpoint: str = None):
        """Réinitialiser le rate limiting pour un agent ou endpoint"""
        if agent_id and endpoint:
            self.request_history[endpoint][agent_id].clear()
            logger.info(f"Rate limit reset for agent {agent_id} on endpoint {endpoint}")
        elif agent_id:
            for ep in self.request_history:
                self.request_history[ep][agent_id].clear()
            logger.info(f"Rate limit reset for agent {agent_id} on all endpoints")
        else:
            self.request_history.clear()
            logger.info("All rate limits reset")


# Instance globale du rate limiter
rate_limiter = RateLimiter()
