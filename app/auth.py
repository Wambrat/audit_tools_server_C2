from fastapi import HTTPException, status
from .db import get_db
from .logger import get_logger

logger = get_logger(__name__)


def verify_agent_credentials(agent_id: str, api_key: str):
    """
    Vérifier les credentials d'un agent.
    Lève une exception si l'authentification échoue.
    """
    db = get_db()
    
    if not agent_id or not api_key:
        logger.warning("Authentication attempt with missing credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing agent credentials"
        )
    
    if not db.authenticate_agent(agent_id, api_key):
        logger.warning(f"Authentication failed for agent {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent credentials"
        )
    
    agent = db.get_agent(agent_id)
    if not agent:
        logger.warning("Authentication failed - agent not found", agent_id=agent_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found"
        )
    
    logger.debug(f"Agent {agent_id} authenticated successfully")
    return agent
