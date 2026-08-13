"""
Système de monitoring pour tracker l'état global du système C2.
Fournit des stats agrégées sur les agents, tâches et résultats.
"""
from typing import Dict, List
from datetime import datetime, timedelta
from .db import get_db
from .logger import get_logger

logger = get_logger(__name__)


def get_system_overview() -> Dict:
    """
    Récupérer une vue d'ensemble du système.
    """
    db = get_db()
    agents = db.list_agents()
    tasks = db.list_tasks()
    results_all = list(db.results.values())
    
    # Debug logging
    logger.info(f"=== SYSTEM OVERVIEW DEBUG ===")
    logger.info(f"Total agents: {len(agents)}")
    for agent in agents:
        status_value = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)
        logger.info(f"  Agent {agent.agent_id[:8]}: status={status_value}, type={type(agent.status)}, raw={agent.status}")
    
    # Compter les tâches par statut
    task_stats = {
        "pending": len([t for t in tasks if t.status.value == "pending"]),
        "assigned": len([t for t in tasks if t.status.value == "assigned"]),
        "completed": len([t for t in tasks if t.status.value == "completed"]),
        "failed": len([t for t in tasks if t.status.value == "failed"]),
    }
    
    # Compter les agents par statut
    def get_agent_status_value(agent):
        """Helper pour récupérer la valeur du statut de l'agent"""
        if hasattr(agent.status, 'value'):
            return agent.status.value
        return str(agent.status).lower()
    
    agent_stats = {
        "active": len([a for a in agents if get_agent_status_value(a) == "active"]),
        "inactive": len([a for a in agents if get_agent_status_value(a) == "inactive"]),
        "compromised": len([a for a in agents if get_agent_status_value(a) == "compromised"]),
    }
    
    logger.info(f"Agent stats: {agent_stats}")
    
    # Stats des résultats
    results_stats = {
        "success": len([r for r in results_all if r.status == "success"]),
        "failed": len([r for r in results_all if r.status == "failed"]),
    }
    
    # Calculer le taux de succès (0-1)
    success_rate = (
        results_stats["success"] / len(results_all)
        if results_all else 0
    )
    
    # Calculer les temps moyens
    if results_all:
        avg_execution_time = sum(r.execution_time_ms for r in results_all) / len(results_all)
    else:
        avg_execution_time = 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "total": len(agents),
            "by_status": agent_stats
        },
        "tasks": {
            "total": len(tasks),
            "by_status": task_stats
        },
        "results": {
            "total": len(results_all),
            "by_status": results_stats,
            "success_rate": round(success_rate, 3),  # 0-1 (le frontend multiplie par 100)
            "avg_execution_time_ms": round(avg_execution_time, 2)
        }
    }


def get_agents_dashboard() -> Dict:
    """
    Récupérer le dashboard détaillé des agents.
    """
    db = get_db()
    agents = db.list_agents()
    
    agent_list = []
    for agent in agents:
        # Récupérer les stats de beacon
        beacon_stats = db.get_beacon_stats(agent.agent_id)
        
        # Récupérer les tâches assignées
        agent_tasks = db.list_tasks(agent.agent_id)
        task_summary = {
            "pending": len([t for t in agent_tasks if t.status.value == "pending"]),
            "assigned": len([t for t in agent_tasks if t.status.value == "assigned"]),
            "completed": len([t for t in agent_tasks if t.status.value == "completed"]),
            "failed": len([t for t in agent_tasks if t.status.value == "failed"]),
        }
        
        # Récupérer les résultats
        agent_results = db.get_results_by_agent(agent.agent_id) or []
        
        # Déterminer l'état d'activité
        if agent.last_beacon:
            time_since_last_beacon = datetime.now() - agent.last_beacon
            is_inactive = time_since_last_beacon > timedelta(hours=1)
        else:
            is_inactive = True
        
        agent_list.append({
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "hostname": agent.hostname,
            "username": agent.username,
            "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status).lower(),
            "os_version": agent.os_version,
            "is_inactive": is_inactive,
            "created_at": agent.created_at.isoformat(),
            "last_beacon": agent.last_beacon.isoformat() if agent.last_beacon else None,
            "beacon_stats": beacon_stats,
            "tasks": task_summary,
            "results_count": len(agent_results),
            "success_rate": (
                len([r for r in agent_results if r.status == "success"]) / len(agent_results) * 100
                if agent_results else 0
            )
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_agents": len(agents),
        "agents": agent_list
    }


def get_tasks_dashboard() -> Dict:
    """
    Récupérer le dashboard détaillé des tâches.
    """
    db = get_db()
    tasks = db.list_tasks()
    
    # Créer une liste plate de toutes les tâches avec infos
    all_tasks_list = []
    
    # Grouper par agent
    tasks_by_agent = {}
    for task in tasks:
        task_data = {
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "command": task.command,
            "status": str(task.status),
            "priority": task.priority,
            "timeout_seconds": task.timeout_seconds,
            "created_at": task.created_at.isoformat(),
            "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
        all_tasks_list.append(task_data)
        
        if task.agent_id not in tasks_by_agent:
            tasks_by_agent[task.agent_id] = []
        tasks_by_agent[task.agent_id].append(task_data)
    
    # Calculer les temps d'exécution moyens
    completed_tasks = [t for t in tasks if t.status.value == "completed" and t.completed_at]
    avg_execution_time = 0
    if completed_tasks:
        avg_execution_time = sum(
            (t.completed_at - t.created_at).total_seconds() 
            for t in completed_tasks
        ) / len(completed_tasks)
    
    # Stats globales
    task_stats = {
        "pending": len([t for t in tasks if t.status.value == "pending"]),
        "assigned": len([t for t in tasks if t.status.value == "assigned"]),
        "completed": len([t for t in tasks if t.status.value == "completed"]),
        "failed": len([t for t in tasks if t.status.value == "failed"]),
    }
    
    # Tâches en retard (assignées depuis > timeout)
    overdue_tasks = []
    for task in tasks:
        if str(task.status) == "assigned" and task.assigned_at:
            time_assigned = datetime.now() - task.assigned_at
            if time_assigned.total_seconds() > task.timeout_seconds:
                overdue_tasks.append(task.task_id)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tasks": len(tasks),
        "tasks": all_tasks_list,  # Liste plate pour le frontend
        "by_status": task_stats,
        "avg_execution_time_seconds": round(avg_execution_time, 2),
        "overdue_tasks_count": len(overdue_tasks),
        "overdue_task_ids": overdue_tasks,
        "tasks_by_agent": {
            agent_id: {
                "count": len(tasks_list),
                "tasks": tasks_list
            }
            for agent_id, tasks_list in tasks_by_agent.items()
        }
    }



def get_results_dashboard() -> Dict:
    """
    Récupérer le dashboard détaillé des résultats.
    """
    db = get_db()
    results = list(db.results.values())
    agents = {agent.agent_id: agent for agent in db.list_agents()}
    
    # Grouper par agent et enrichir avec infos
    results_by_agent = {}
    all_results_list = []
    
    for result in results:
        agent = agents.get(result.agent_id)
        agent_name = agent.agent_name if agent else "Unknown Agent"
        
        result_data = {
            "result_id": result.result_id,
            "task_id": result.task_id,
            "agent_id": result.agent_id,
            "agent_name": agent_name,
            "status": result.status,
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message,
            "created_at": result.created_at.isoformat(),
            "result": result.result,  # Contenu du résultat
            "result_preview": result.result_preview,  # Aperçu du résultat
        }
        
        all_results_list.append(result_data)
        
        if result.agent_id not in results_by_agent:
            results_by_agent[result.agent_id] = {
                "agent_name": agent_name,
                "results": []
            }
        results_by_agent[result.agent_id]["results"].append(result_data)
    
    # Stats globales
    success_count = len([r for r in results if r.status == "success"])
    failed_count = len([r for r in results if r.status == "failed"])
    
    success_rate = (
        success_count / len(results) * 100 if results else 0
    )
    
    # Temps d'exécution moyen
    avg_execution_time = (
        sum(r.execution_time_ms for r in results) / len(results)
        if results else 0
    )
    
    # Résultats avec erreurs
    failed_results = [
        {
            "result_id": r.result_id,
            "task_id": r.task_id,
            "agent_id": r.agent_id,
            "agent_name": agents.get(r.agent_id, agent).agent_name if agents.get(r.agent_id) else "Unknown",
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat()
        }
        for r in results if r.status == "failed"
    ]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results),
        "success": {
            "count": success_count,
            "rate_percent": round(success_rate, 2)
        },
        "failed": {
            "count": failed_count,
            "rate_percent": round(100 - success_rate, 2),
            "details": failed_results[:10]
        },
        "avg_execution_time_ms": round(avg_execution_time, 2),
        "results": all_results_list,
        "results_by_agent": {
            agent_id: {
                "agent_name": data["agent_name"],
                "count": len(data["results"]),
                "success": len([r for r in data["results"] if r["status"] == "success"]),
                "failed": len([r for r in data["results"] if r["status"] == "failed"]),
                "results": data["results"]
            }
            for agent_id, data in results_by_agent.items()
        }
    }


def get_alerts() -> Dict:
    """
    Récupérer les alertes et problèmes détectés.
    """
    db = get_db()
    alerts = []
    
    # Détecter les agents inactifs
    agents = db.list_agents()
    for agent in agents:
        if agent.last_beacon:
            time_since_last_beacon = datetime.now() - agent.last_beacon
            if time_since_last_beacon > timedelta(hours=2):
                alerts.append({
                    "level": "critical",
                    "type": "agent_inactive",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": f"Agent inactive for {time_since_last_beacon.total_seconds() / 3600:.1f} hours",
                    "timestamp": datetime.now().isoformat()
                })
            elif time_since_last_beacon > timedelta(minutes=30):
                alerts.append({
                    "level": "warning",
                    "type": "agent_slow",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": f"Agent not responded for {time_since_last_beacon.total_seconds() / 60:.1f} minutes",
                    "timestamp": datetime.now().isoformat()
                })
        else:
            # Agent never beaconed
            time_since_creation = datetime.now() - agent.created_at
            if time_since_creation > timedelta(hours=1):
                alerts.append({
                    "level": "critical",
                    "type": "agent_never_beaconed",
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "message": f"Agent created but never beaconed",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Détecter les tâches en retard
    tasks = db.list_tasks()
    for task in tasks:
        if str(task.status) == "assigned" and task.assigned_at:
            time_assigned = datetime.now() - task.assigned_at
            if time_assigned.total_seconds() > task.timeout_seconds:
                alerts.append({
                    "level": "warning",
                    "type": "task_timeout",
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                    "message": f"Task timeout exceeded by {time_assigned.total_seconds() - task.timeout_seconds:.0f}s",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Déterminer le niveau global d'alerte
    critical_alerts = len([a for a in alerts if a["level"] == "critical"])
    warning_alerts = len([a for a in alerts if a["level"] == "warning"])
    
    overall_level = "ok"
    if critical_alerts > 0:
        overall_level = "critical"
    elif warning_alerts > 0:
        overall_level = "warning"
    
    return {
        "timestamp": datetime.now().isoformat(),
        "overall_level": overall_level,
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "alerts": alerts
    }
