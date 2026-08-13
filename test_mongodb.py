#!/usr/bin/env python3
"""
Script de test MongoDB

Vérifie que MongoDB fonctionne correctement et que la connexion est établie.
Utile pour diagnostiquer les problèmes de configuration.

Usage:
    python test_mongodb.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.logger import get_logger
from app.database_mongodb import MongoDatabase
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


def test_connection():
    """Tester la connexion MongoDB"""
    try:
        logger.info("🔗 Test de connexion MongoDB...")
        
        db = MongoDatabase()
        
        logger.info("✅ Connexion établie avec succès!")
        return db
        
    except Exception as e:
        logger.error(f"❌ Erreur de connexion: {e}")
        return None


def test_operations(db):
    """Tester les opérations basiques"""
    
    logger.info("\n📊 Test des opérations CRUD...")
    
    # Test 1: Créer un agent de test
    logger.info("\n1️⃣ Création d'un agent de test...")
    try:
        agent = db.create_agent(
            agent_name="TEST-AGENT",
            os_version="Windows 10",
            hostname="TEST-PC",
            username="tester"
        )
        logger.info(f"✅ Agent créé: {agent.agent_id}")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 2: Récupérer l'agent
    logger.info("\n2️⃣ Récupération de l'agent...")
    try:
        fetched = db.get_agent(agent.agent_id)
        if fetched:
            logger.info(f"✅ Agent trouvé: {fetched.agent_name}")
        else:
            logger.error("❌ Agent non trouvé!")
            return False
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 3: Créer une tâche
    logger.info("\n3️⃣ Création d'une tâche...")
    try:
        task = db.create_task(
            agent_id=agent.agent_id,
            command="Get-Processes",
            parameters=None,
            priority=0
        )
        logger.info(f"✅ Tâche créée: {task.task_id}")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 4: Obtenir les tâches en attente
    logger.info("\n4️⃣ Récupération des tâches en attente...")
    try:
        pending = db.get_pending_tasks(agent.agent_id)
        logger.info(f"✅ {len(pending)} tâche(s) en attente")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 5: Enregistrer un beacon
    logger.info("\n5️⃣ Enregistrement d'un beacon...")
    try:
        db.record_beacon(
            agent_id=agent.agent_id,
            status="online",
            uptime_seconds=3600,
            ip_address="192.168.1.100"
        )
        logger.info("✅ Beacon enregistré")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 6: Soumettre un résultat
    logger.info("\n6️⃣ Soumission d'un résultat...")
    try:
        result = db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            status="success",
            result={"processes": ["notepad.exe", "cmd.exe"]},
            execution_time_ms=125
        )
        logger.info(f"✅ Résultat enregistré: {result.result_id}")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    # Test 7: Obtenir les statistiques
    logger.info("\n7️⃣ Récupération des statistiques...")
    try:
        stats = db.get_stats()
        logger.info(f"✅ Statistiques: {stats}")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False
    
    return True


def test_indexes(db):
    """Vérifier les index"""
    logger.info("\n📑 Vérification des index...")
    
    collections = {
        "agents": db.agents,
        "tasks": db.tasks,
        "audit_results": db.results,
        "beacon_history": db.beacons
    }
    
    for name, collection in collections.items():
        try:
            indexes = collection.list_indexes()
            index_list = list(indexes)
            logger.info(f"✅ {name}: {len(index_list)} index(es)")
            for idx in index_list:
                logger.info(f"   - {idx['key']}")
        except Exception as e:
            logger.error(f"❌ {name}: {e}")


def cleanup(db):
    """Nettoyer les données de test"""
    logger.info("\n🧹 Nettoyage des données de test...")
    try:
        # Supprimer les collections de test
        # (garder les données pour l'inspection)
        logger.info("✅ Données conservées pour inspection")
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")


def main():
    """Exécuter tous les tests"""
    logger.info("=" * 60)
    logger.info("🧪 TEST MONGODB")
    logger.info("=" * 60)
    
    # Test 1: Connexion
    db = test_connection()
    if not db:
        logger.error("\n❌ Les tests ont échoué!")
        return False
    
    # Test 2: Opérations
    if not test_operations(db):
        logger.error("\n❌ Les opérations ont échoué!")
        return False
    
    # Test 3: Index
    test_indexes(db)
    
    # Nettoyage
    cleanup(db)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ TOUS LES TESTS RÉUSSIS!")
    logger.info("=" * 60)
    logger.info("\nMongoDB est prêt à être utilisé.\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
