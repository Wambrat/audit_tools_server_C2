#!/usr/bin/env python3
"""
Script de migration: Mémoire → MongoDB

Migre les données du système en mémoire vers MongoDB.
Utile pour la transition depuis le mode développement au mode production.

Usage:
    python migrate_to_mongodb.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import db as memory_db
from app.database_mongodb import db_instance
from app.logger import get_logger

logger = get_logger(__name__)


def migrate_agents():
    """Migrer tous les agents"""
    agents = memory_db.list_agents()
    
    if not agents:
        logger.info("Aucun agent à migrer")
        return 0
    
    count = 0
    for agent in agents:
        try:
            db_instance.agents.insert_one({
                "agent_id": agent.agent_id,
                "api_key": agent.api_key,
                "agent_name": agent.agent_name,
                "os_version": agent.os_version,
                "hostname": agent.hostname,
                "username": agent.username,
                "status": agent.status,
                "created_at": agent.created_at,
                "last_beacon": agent.last_beacon,
            })
            count += 1
        except Exception as e:
            logger.error(f"Erreur migration agent {agent.agent_id}: {e}")
    
    logger.info(f"✓ {count} agents migrés")
    return count


def migrate_tasks():
    """Migrer toutes les tâches"""
    tasks = memory_db.list_tasks()
    
    if not tasks:
        logger.info("Aucune tâche à migrer")
        return 0
    
    count = 0
    for task in tasks:
        try:
            db_instance.tasks.insert_one({
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "command": task.command,
                "parameters": task.parameters,
                "priority": task.priority,
                "status": task.status,
                "timeout_seconds": task.timeout_seconds,
                "created_at": task.created_at,
                "assigned_at": task.assigned_at,
                "completed_at": task.completed_at,
            })
            count += 1
        except Exception as e:
            logger.error(f"Erreur migration tâche {task.task_id}: {e}")
    
    logger.info(f"✓ {count} tâches migrées")
    return count


def migrate_results():
    """Migrer tous les résultats"""
    results = list(memory_db.results.values())
    
    if not results:
        logger.info("Aucun résultat à migrer")
        return 0
    
    count = 0
    for result in results:
        try:
            db_instance.results.insert_one({
                "result_id": result.result_id,
                "task_id": result.task_id,
                "agent_id": result.agent_id,
                "status": result.status,
                "result": result.result,
                "execution_time_ms": result.execution_time_ms,
                "error_message": result.error_message,
                "created_at": result.created_at,
            })
            count += 1
        except Exception as e:
            logger.error(f"Erreur migration résultat {result.result_id}: {e}")
    
    logger.info(f"✓ {count} résultats migrés")
    return count


def migrate_beacons():
    """Migrer tous les beacons"""
    beacons = list(memory_db.beacon_history.values())
    
    if not beacons:
        logger.info("Aucun beacon à migrer")
        return 0
    
    count = 0
    for beacon_list in beacons:
        for beacon in beacon_list:
            try:
                db_instance.beacons.insert_one({
                    "beacon_id": beacon.beacon_id,
                    "agent_id": beacon.agent_id,
                    "beacon_status": beacon.beacon_status,
                    "uptime_seconds": beacon.uptime_seconds,
                    "tasks_count": beacon.tasks_count,
                    "ip_address": beacon.ip_address,
                    "created_at": beacon.created_at,
                })
                count += 1
            except Exception as e:
                logger.error(f"Erreur migration beacon {beacon.beacon_id}: {e}")
    
    logger.info(f"✓ {count} beacons migrés")
    return count


def main():
    """Exécuter la migration complète"""
    if db_instance is None:
        logger.error("✗ MongoDB n'est pas disponible!")
        logger.error("Vérifiez que MongoDB est en cours d'exécution et que MONGODB_URL est correct")
        return False
    
    logger.info("=" * 60)
    logger.info("🔄 MIGRATION: Mémoire → MongoDB")
    logger.info("=" * 60)
    
    try:
        logger.info("Migration des données...")
        
        agents_count = migrate_agents()
        tasks_count = migrate_tasks()
        results_count = migrate_results()
        beacons_count = migrate_beacons()
        
        logger.info("=" * 60)
        logger.info("✓ Migration terminée avec succès!")
        logger.info(f"  - {agents_count} agents")
        logger.info(f"  - {tasks_count} tâches")
        logger.info(f"  - {results_count} résultats")
        logger.info(f"  - {beacons_count} beacons")
        logger.info("=" * 60)
        
        stats = db_instance.get_stats()
        logger.info(f"Total MongoDB: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erreur lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
