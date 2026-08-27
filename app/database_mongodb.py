"""
Couche de base de donnÃ©es MongoDB pour le serveur jadus.
Remplace l'implÃ©mentation en mÃ©moire par une vraie base de donnÃ©es persistante.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from .models import Agent, Task, AuditResult, BeaconHistory, AuditTemplate, PowerShellCommandDefinition
from .logger import get_logger
from datetime import datetime
import os
import re
import uuid

logger = get_logger(__name__)

# Configuration MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "jadus_server")
MONGODB_TIMEOUT = int(os.getenv("MONGODB_TIMEOUT", 5000))  # ms

# Configuration TLS (optionnel)
MONGODB_TLS_ENABLED = os.getenv("MONGODB_TLS_ENABLED", "false").lower() == "true"
MONGODB_TLS_CA_FILE = os.getenv("MONGODB_TLS_CA_FILE", "/etc/mongodb/ca.pem")

logger.info(f"MongoDB TLS Configuration - Enabled: {MONGODB_TLS_ENABLED}, CA File: {MONGODB_TLS_CA_FILE}")

try:
    # Configuration client MongoDB
    client_kwargs = {
        "serverSelectionTimeoutMS": MONGODB_TIMEOUT,
        "connectTimeoutMS": MONGODB_TIMEOUT,
    }
    
    # Ajouter TLS si activÃ©
    if MONGODB_TLS_ENABLED:
        if os.path.exists(MONGODB_TLS_CA_FILE):
            client_kwargs["tlsCAFile"] = MONGODB_TLS_CA_FILE
            client_kwargs["tlsAllowInvalidCertificates"] = False
            client_kwargs["tlsAllowInvalidHostnames"] = True  # Pour certificats auto-signÃ©s
            logger.info(f"ðŸ” MongoDB TLS enabled with CA: {MONGODB_TLS_CA_FILE}")
        else:
            logger.warning(f"âš ï¸ TLS CA file not found: {MONGODB_TLS_CA_FILE}")
    
    # Connexion Ã  MongoDB
    client = MongoClient(MONGODB_URI, **client_kwargs)
    
    # VÃ©rifier la connexion
    client.admin.command("ping")
    logger.info(f"âœ“ ConnectÃ© Ã  MongoDB: {MONGODB_URI.split('://')[1].split('@')[0]}@{MONGODB_URI.split('@')[1] if '@' in MONGODB_URI else 'local'}")
    
    db = client[MONGODB_DB]
    
except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    logger.error(f"âœ— Connexion MongoDB Ã©chouÃ©e: {e}")
    logger.warning("Utilisant le mode fallback (mÃ©moire)")
    db = None
except Exception as e:
    logger.error(f"âœ— Erreur MongoDB: {e}")
    logger.warning("Utilisant le mode fallback (mÃ©moire)")
    db = None


class MongoDatabase:
    """Interface MongoDB pour l'API jadus"""
    
    def __init__(self):
        """Initialiser les collections et les index"""
        if db is None:
            raise RuntimeError("MongoDB non disponible")
        
        self.agents = db.agents
        self.tasks = db.tasks
        self.results = db.audit_results
        self.beacons = db.beacon_history
        self.audit_templates = db.audit_templates
        self.powershell_commands = db.powershell_commands
        self.template_history = db.template_history
        
        self._create_indexes()
        logger.info("âœ“ Collections MongoDB initialisÃ©es")
    
    def _create_indexes(self):
        """CrÃ©er les index pour optimiser les requÃªtes"""
        try:
            # Agents
            self.agents.create_index("agent_id", unique=True)
            self.agents.create_index("api_key", unique=True)
            self.agents.create_index("created_at")
            self.agents.create_index("last_beacon")
            
            # Tasks
            self.tasks.create_index("task_id", unique=True)
            self.tasks.create_index("agent_id")
            self.tasks.create_index([("agent_id", ASCENDING), ("status", ASCENDING)])
            self.tasks.create_index("created_at")
            self.tasks.create_index("status")
            
            # Results
            self.results.create_index("result_id", unique=True)
            self.results.create_index("task_id")
            self.results.create_index("agent_id")
            self.results.create_index([("agent_id", ASCENDING), ("created_at", DESCENDING)])
            self.results.create_index("created_at")
            
            # Beacons
            self.beacons.create_index("beacon_id", unique=True)
            self.beacons.create_index("agent_id")
            self.beacons.create_index([("agent_id", ASCENDING), ("created_at", DESCENDING)])
            self.beacons.create_index("created_at")

            # Audit templates
            self.audit_templates.create_index("template_id", unique=True)
            self.audit_templates.create_index("created_by")
            self.audit_templates.create_index("enabled")

            # PowerShell commands
            self.powershell_commands.create_index("command_id", unique=True)
            self.powershell_commands.create_index("name", unique=True)
            self.powershell_commands.create_index("created_by")
            self.powershell_commands.create_index("enabled")

            # Template usage history
            self.template_history.create_index("template_id")
            self.template_history.create_index("agent_id")
            self.template_history.create_index("applied_at")
            
            logger.info("âœ“ Index MongoDB crÃ©Ã©s")
        except Exception as e:
            logger.error(f"Erreur crÃ©ation des index: {e}")
    
    # ===== AGENTS =====
    
    def create_agent(self, agent_name: str, os_version: str, hostname: str, username: str) -> Agent:
        """CrÃ©er un nouvel agent"""
        agent_id = str(uuid.uuid4())
        api_key = str(uuid.uuid4())
        now = datetime.now()
        
        agent_doc = {
            "agent_id": agent_id,
            "api_key": api_key,
            "agent_name": agent_name,
            "os_version": os_version,
            "hostname": hostname,
            "username": username,
            "status": "active",
            "created_at": now,
            "last_beacon": None,
        }
        
        self.agents.insert_one(agent_doc)
        logger.info(f"Agent crÃ©Ã©: {agent_id} ({agent_name})")
        
        return Agent(**agent_doc)
    
    def get_agent(self, agent_id: str) -> Agent:
        """RÃ©cupÃ©rer un agent par ID"""
        doc = self.agents.find_one({"agent_id": agent_id})
        if doc:
            doc.pop("_id", None)  # Retirer l'ID MongoDB
            return Agent(**doc)
        return None
    
    def list_agents(self) -> list:
        """Lister tous les agents"""
        docs = list(self.agents.find({}))
        for doc in docs:
            doc.pop("_id", None)
        return [Agent(**doc) for doc in docs]
    
    def update_agent_beacon(self, agent_id: str) -> bool:
        """Mettre Ã  jour le dernier beacon d'un agent et le marquer comme actif"""
        result = self.agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"last_beacon": datetime.now(), "status": "active"}}
        )
        return result.modified_count > 0
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Mettre Ã  jour le statut d'un agent"""
        result = self.agents.update_one(
            {"agent_id": agent_id},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    def delete_agent(self, agent_id: str) -> bool:
        """Supprimer un agent et toutes ses tÃ¢ches et rÃ©sultats associÃ©s"""
        # VÃ©rifier que l'agent existe
        agent = self.agents.find_one({"agent_id": agent_id})
        if not agent:
            return False
        
        # Supprimer l'agent
        self.agents.delete_one({"agent_id": agent_id})
        
        # Supprimer toutes ses tÃ¢ches
        self.tasks.delete_many({"agent_id": agent_id})
        
        # Supprimer tous ses rÃ©sultats
        self.results.delete_many({"agent_id": agent_id})
        
        # Supprimer l'historique des beacons
        if hasattr(self, 'beacon_history'):
            self.beacon_history.delete_many({"agent_id": agent_id})
        
        return True
    
    # ===== TASKS =====
    
    def _normalize_task_parameters(self, parameters: dict = None) -> dict:
        """Normaliser les paramÃ¨tres pour garantir un format JSON standard."""
        if parameters is None:
            return None

        if not isinstance(parameters, dict):
            try:
                parameters = dict(parameters)
            except (TypeError, ValueError):
                return {"raw": str(parameters)}

        normalized = {}
        for key, value in parameters.items():
            if value is None or isinstance(value, (str, int, float, bool, list, dict)):
                normalized[key] = value
            else:
                normalized[key] = str(value)
        return normalized

    def _attach_command_script_to_parameters(self, command_name: str, parameters: dict = None) -> dict:
        """Ajoute le script PowerShell associÃ© Ã  une commande enregistrÃ©e dans la tÃ¢che."""
        normalized_parameters = self._normalize_task_parameters(parameters)
        if not normalized_parameters:
            normalized_parameters = {}

        command_def = self.get_powershell_command_by_name(command_name)
        if command_def and command_def.script and str(command_def.script).strip():
            normalized_parameters.setdefault("script", command_def.script)
            normalized_parameters.setdefault("script_body", command_def.script)
            normalized_parameters.setdefault("command_name", command_name)

        return normalized_parameters

    def create_task(self, agent_id: str, command: str, parameters: dict = None, priority: int = 0) -> Task:
        """CrÃ©er une nouvelle tÃ¢che"""
        task_id = str(uuid.uuid4())
        now = datetime.now()
        normalized_parameters = self._attach_command_script_to_parameters(command, parameters)
        
        task_doc = {
            "task_id": task_id,
            "agent_id": agent_id,
            "command": command,
            "parameters": normalized_parameters,
            "priority": priority,
            "status": "pending",
            "timeout_seconds": 300,
            "created_at": now,
            "assigned_at": None,
            "completed_at": None,
        }
        
        self.tasks.insert_one(task_doc)
        logger.info(f"TÃ¢che crÃ©Ã©e: {task_id} pour agent {agent_id} (commande: {command})")
        
        return Task(**task_doc)
    
    def get_task(self, task_id: str) -> Task:
        """RÃ©cupÃ©rer une tÃ¢che par ID"""
        doc = self.tasks.find_one({"task_id": task_id})
        if doc:
            doc.pop("_id", None)
            return Task(**doc)
        return None
    
    def list_tasks(self) -> list:
        """Lister toutes les tÃ¢ches"""
        docs = list(self.tasks.find({}))
        for doc in docs:
            doc.pop("_id", None)
        return [Task(**doc) for doc in docs]
    
    def get_pending_tasks(self, agent_id: str) -> list:
        """RÃ©cupÃ©rer les tÃ¢ches en attente pour un agent"""
        docs = list(self.tasks.find({
            "agent_id": agent_id,
            "status": {"$in": ["pending", "assigned"]}
        }).sort("priority", DESCENDING).sort("created_at", ASCENDING))
        
        for doc in docs:
            doc.pop("_id", None)
        
        return [Task(**doc) for doc in docs]
    
    def update_task_status(self, task_id: str, status: str, completed_at: datetime = None) -> bool:
        """Mettre Ã  jour le statut d'une tÃ¢che"""
        update_data = {"$set": {"status": status}}
        if completed_at:
            update_data["$set"]["completed_at"] = completed_at
        
        result = self.tasks.update_one(
            {"task_id": task_id},
            update_data
        )
        return result.modified_count > 0
    
    # ===== AUDIT RESULTS =====
    
    def store_result(self, task_id: str, agent_id: str, status: str, result: dict, 
                    execution_time_ms: int, error_message: str = None) -> AuditResult:
        """Enregistrer un rÃ©sultat d'audit"""
        result_id = str(uuid.uuid4())
        now = datetime.now()
        
        result_doc = {
            "result_id": result_id,
            "task_id": task_id,
            "agent_id": agent_id,
            "status": status,
            "result": result,  # JSON brut de PowerShell
            "execution_time_ms": execution_time_ms,
            "error_message": error_message,
            "created_at": now,
        }
        
        self.results.insert_one(result_doc)
        
        # Mettre Ã  jour le statut de la tÃ¢che
        self.update_task_status(task_id, "completed", now)
        
        logger.info(f"RÃ©sultat enregistrÃ©: {result_id} pour tÃ¢che {task_id} (status: {status})")
        
        return AuditResult(**result_doc)
    
    def get_results(self, agent_id: str) -> list:
        """RÃ©cupÃ©rer tous les rÃ©sultats d'un agent"""
        docs = list(self.results.find({"agent_id": agent_id}).sort("created_at", DESCENDING))
        for doc in docs:
            doc.pop("_id", None)
        return [AuditResult(**doc) for doc in docs]
    
    def get_result(self, result_id: str) -> AuditResult:
        """RÃ©cupÃ©rer un rÃ©sultat par ID"""
        doc = self.results.find_one({"result_id": result_id})
        if doc:
            doc.pop("_id", None)
            return AuditResult(**doc)
        return None

    @staticmethod
    def _normalize_command_name(command_name: str) -> str:
        return str(command_name or '').strip()

    def _get_valid_command_names(self) -> set:
        builtins = {
            "Get-Process", "Get-Service", "Get-AuditPolicy", "Get-LocalUser",
            "Get-LocalGroup", "Get-IPConfig", "Get-EventLog", "SystemInfo",
            "Get-NetAdapter", "Get-ChildItem", "Get-ComputerInfo"
        }
        custom_names = {cmd["name"] for cmd in self.powershell_commands.find({"enabled": True})}
        return builtins | custom_names

    def create_powershell_command(self, name: str, description: str = "", script: str = "", created_by: str = "admin") -> PowerShellCommandDefinition:
        """CrÃ©er une commande PowerShell rÃ©utilisable."""
        normalized_name = self._normalize_command_name(name)
        if not normalized_name:
            raise ValueError("Le nom de la commande est obligatoire")
        if not str(script or '').strip():
            raise ValueError("Le script PowerShell ne peut pas Ãªtre vide")
        if self.powershell_commands.find_one({"name": {"$regex": f"^{re.escape(normalized_name)}$", "$options": "i"}}):
            raise ValueError(f"Une commande nommÃ©e '{normalized_name}' existe dÃ©jÃ ")

        command_id = str(uuid.uuid4())
        now = datetime.now()
        command_doc = {
            "command_id": command_id,
            "name": normalized_name,
            "description": (description or '').strip(),
            "script": str(script).strip(),
            "created_by": (created_by or 'admin').strip() or 'admin',
            "created_at": now,
            "enabled": True,
        }
        self.powershell_commands.insert_one(command_doc)
        logger.info(f"PowerShell command created in MongoDB: {normalized_name}")
        return PowerShellCommandDefinition(**command_doc)

    def list_powershell_commands(self) -> list:
        docs = list(self.powershell_commands.find({}).sort("created_at", DESCENDING))
        for doc in docs:
            doc.pop("_id", None)
        return [PowerShellCommandDefinition(**doc) for doc in docs]

    def get_powershell_command(self, command_id: str) -> PowerShellCommandDefinition:
        doc = self.powershell_commands.find_one({"command_id": command_id})
        if doc:
            doc.pop("_id", None)
            return PowerShellCommandDefinition(**doc)
        return None

    def update_powershell_command(self, command_id: str, name: str, description: str = "", script: str = "", created_by: str = "admin") -> PowerShellCommandDefinition:
        command = self.get_powershell_command(command_id)
        if not command:
            raise ValueError("Commande PowerShell introuvable")

        normalized_name = self._normalize_command_name(name)
        if not normalized_name:
            raise ValueError("Le nom de la commande est obligatoire")
        if not str(script or '').strip():
            raise ValueError("Le script PowerShell ne peut pas Ãªtre vide")
        duplicate = self.powershell_commands.find_one({"command_id": {"$ne": command_id}, "name": {"$regex": f"^{re.escape(normalized_name)}$", "$options": "i"}})
        if duplicate:
            raise ValueError(f"Une commande nommÃ©e '{normalized_name}' existe dÃ©jÃ ")

        updated_doc = {
            "name": normalized_name,
            "description": (description or '').strip(),
            "script": str(script).strip(),
            "created_by": (created_by or command.created_by).strip() or command.created_by,
            "enabled": True,
        }
        self.powershell_commands.update_one({"command_id": command_id}, {"$set": updated_doc})
        return self.get_powershell_command(command_id)

    def delete_powershell_command(self, command_id: str) -> bool:
        result = self.powershell_commands.delete_one({"command_id": command_id})
        return result.deleted_count > 0

    def seed_default_modules(self, zip_path: str = None) -> dict:
        """Importer les modules PowerShell standards prÃ©sents dans modules.zip dans la DB MongoDB."""
        import os
        import zipfile
        from pathlib import Path

        if zip_path is None:
            zip_path = str(Path(__file__).resolve().parent.parent / "modules.zip")

        if not os.path.exists(zip_path):
            logger.warning(f"Archive modules introuvable: {zip_path}")
            return {"commands": 0, "templates": 0}

        command_count = 0
        template_count = 0

        try:
            with zipfile.ZipFile(zip_path) as archive:
                ps1_files = sorted([
                    name for name in archive.namelist()
                    if name.lower().endswith('.ps1') and 'TEMP/' not in name.lower()
                ])

                for relative_name in ps1_files:
                    script_name = os.path.basename(relative_name)
                    command_name = script_name[:-4]
                    script_content = archive.read(relative_name).decode('utf-8', errors='replace')

                    if command_name.startswith('Get-') or command_name.startswith('Test-') or command_name.startswith('Set-'):
                        try:
                            existing = self.powershell_commands.find_one({"name": {"$regex": f"^{re.escape(command_name)}$", "$options": "i"}})
                            if existing is None:
                                self.powershell_commands.insert_one({
                                    "command_id": str(uuid.uuid4()),
                                    "name": command_name,
                                    "description": f"Module importÃ© depuis {relative_name}",
                                    "script": script_content,
                                    "created_by": "system",
                                    "created_at": datetime.now(),
                                    "enabled": True,
                                })
                                command_count += 1
                        except Exception:
                            continue

                if command_count > 0:
                    grouped = {}
                    for relative_name in ps1_files:
                        folder = relative_name.split('/')[0] if '/' in relative_name else 'General'
                        grouped.setdefault(folder, []).append(os.path.splitext(os.path.basename(relative_name))[0])

                    for folder_name, names in sorted(grouped.items()):
                        if not names:
                            continue
                        if self.audit_templates.find_one({"name": folder_name + " Audit"}):
                            continue
                        try:
                            self.audit_templates.insert_one({
                                "template_id": str(uuid.uuid4()),
                                "name": f"{folder_name} Audit",
                                "description": f"Template initialisÃ© depuis les modules {folder_name}",
                                "commands": names[:8],
                                "created_by": "system",
                                "created_at": datetime.now(),
                                "enabled": True,
                            })
                            template_count += 1
                        except Exception:
                            continue

            logger.info(f"Modules importÃ©s en MongoDB: {command_count} commandes, {template_count} templates")
            return {"commands": command_count, "templates": template_count}
        except Exception as exc:
            logger.error(f"Erreur lors de l'import des modules par dÃ©faut MongoDB: {exc}")
            return {"commands": 0, "templates": 0}

    # ===== AUDIT TEMPLATES =====

    def create_audit_template(self, name: str, description: str, commands: list, created_by: str = "admin") -> AuditTemplate:
        """CrÃ©er une configuration d'audit mongo"""
        cleaned_commands = []
        allowed_commands = self._get_valid_command_names()

        for command in commands:
            normalized = str(command).strip()
            if not normalized:
                continue
            if normalized not in allowed_commands:
                raise ValueError(f"Commande non autorisÃ©e: {normalized}")
            if normalized not in cleaned_commands:
                cleaned_commands.append(normalized)

        if not cleaned_commands:
            raise ValueError("La configuration d'audit doit contenir au moins une commande valide")

        template_id = str(uuid.uuid4())
        now = datetime.now()
        template_doc = {
            "template_id": template_id,
            "name": name.strip(),
            "description": description.strip(),
            "commands": cleaned_commands,
            "created_by": (created_by or "admin").strip(),
            "created_at": now,
            "enabled": True,
        }

        self.audit_templates.insert_one(template_doc)
        logger.info(f"Audit template created in MongoDB: {template_id}")
        return AuditTemplate(**template_doc)

    def list_audit_templates(self) -> list:
        """Lister les templates d'audit"""
        docs = list(self.audit_templates.find({}).sort("created_at", DESCENDING))
        for doc in docs:
            doc.pop("_id", None)
        return [AuditTemplate(**doc) for doc in docs]

    def get_audit_template(self, template_id: str) -> AuditTemplate:
        """RÃ©cupÃ©rer un template d'audit"""
        doc = self.audit_templates.find_one({"template_id": template_id})
        if doc:
            doc.pop("_id", None)
            return AuditTemplate(**doc)
        return None

    def update_audit_template(self, template_id: str, name: str, description: str, commands: list, created_by: str = "admin") -> AuditTemplate:
        """Mettre Ã  jour un template d'audit existant"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        cleaned_commands = []
        allowed_commands = self._get_valid_command_names()

        for command in commands:
            normalized = str(command).strip()
            if not normalized:
                continue
            if normalized not in allowed_commands:
                raise ValueError(f"Commande non autorisÃ©e: {normalized}")
            if normalized not in cleaned_commands:
                cleaned_commands.append(normalized)

        if not cleaned_commands:
            raise ValueError("La configuration d'audit doit contenir au moins une commande valide")

        updated_doc = {
            "name": (name or template.name).strip(),
            "description": description if description is not None else template.description,
            "commands": cleaned_commands,
            "created_by": (created_by or template.created_by).strip() or template.created_by,
            "enabled": True,
        }

        self.audit_templates.update_one({"template_id": template_id}, {"$set": updated_doc})
        template = self.get_audit_template(template_id)
        logger.info(f"Audit template updated in MongoDB: {template_id}")
        return template

    def duplicate_audit_template(self, template_id: str) -> AuditTemplate:
        """Dupliquer un template d'audit"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        new_template = self.create_audit_template(
            name=f"{template.name} (copie)",
            description=template.description,
            commands=list(template.commands),
            created_by=template.created_by,
        )
        return new_template

    def delete_audit_template(self, template_id: str) -> bool:
        """Supprimer un template d'audit"""
        result = self.audit_templates.delete_one({"template_id": template_id})
        return result.deleted_count > 0

    def export_audit_template(self, template_id: str) -> dict:
        """Exporter les donnÃ©es d'un template au format JSON"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "commands": list(template.commands),
            "created_by": template.created_by,
            "created_at": template.created_at.isoformat(),
            "enabled": template.enabled,
        }

    def record_template_application(self, template_id: str, agent_id: str, task_count: int = 0) -> dict:
        """Historiser l'application d'un template Ã  un agent"""
        entry = {
            "template_id": template_id,
            "agent_id": agent_id,
            "task_count": task_count,
            "applied_at": datetime.now(),
        }
        self.template_history.insert_one(entry)
        return {
            "template_id": template_id,
            "agent_id": agent_id,
            "task_count": task_count,
            "applied_at": entry["applied_at"].isoformat(),
        }

    def get_template_history(self, limit: int = 50) -> list:
        """RÃ©cupÃ©rer l'historique d'application des templates"""
        docs = list(self.template_history.find({}).sort("applied_at", -1).limit(limit))
        for doc in docs:
            doc.pop("_id", None)
            if "applied_at" in doc and hasattr(doc["applied_at"], "isoformat"):
                doc["applied_at"] = doc["applied_at"].isoformat()
        return docs

    def build_tasks_from_template(self, template_id: str, agent_id: str):
        """CrÃ©er des tÃ¢ches standardisÃ©es pour un agent Ã  partir d'un template."""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        created_tasks = []
        total_commands = len(template.commands)

        for index, command in enumerate(template.commands, start=1):
            created_tasks.append(self.create_task(
                agent_id=agent_id,
                command=command,
                parameters={
                    "execution_context": "template",
                    "template_id": template.template_id,
                    "template_name": template.name,
                    "command_name": command,
                    "command_index": index,
                    "command_total": total_commands,
                },
                priority=0,
            ))
        return created_tasks

    def apply_template_to_all_agents(self, template_id: str) -> dict:
        """Appliquer un template Ã  tous les agents connectÃ©s"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        agents = self.list_agents()
        total_tasks = 0
        applied_agents = []

        for agent in agents:
            tasks = self.build_tasks_from_template(template_id, agent.agent_id)
            total_tasks += len(tasks)
            applied_agents.append(agent.agent_id)
            self.record_template_application(template_id, agent.agent_id, len(tasks))

        return {
            "template_id": template_id,
            "agents_total": len(agents),
            "applied_agents": applied_agents,
            "task_count": total_tasks,
            "message": f"Template appliquÃ© Ã  {len(agents)} agent(s)"
        }
    
    # ===== BEACON HISTORY =====
    
    def record_beacon(self, agent_id: str, beacon_status: str, uptime_seconds: int, 
                     tasks_count: int, ip_address: str = None) -> BeaconHistory:
        """Enregistrer un beacon"""
        beacon_id = str(uuid.uuid4())
        now = datetime.now()
        
        beacon_doc = {
            "beacon_id": beacon_id,
            "agent_id": agent_id,
            "beacon_status": beacon_status,
            "uptime_seconds": uptime_seconds,
            "tasks_count": tasks_count,
            "ip_address": ip_address,
            "created_at": now,
        }
        
        self.beacons.insert_one(beacon_doc)
        
        # Mettre Ã  jour last_beacon de l'agent
        self.update_agent_beacon(agent_id)
        
        return BeaconHistory(**beacon_doc)
    
    def get_beacon_history(self, agent_id: str, limit: int = 100) -> list:
        """RÃ©cupÃ©rer l'historique des beacons d'un agent"""
        docs = list(
            self.beacons.find({"agent_id": agent_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
        )
        for doc in docs:
            doc.pop("_id", None)
        return [BeaconHistory(**doc) for doc in docs]
    
    def get_beacon_stats(self, agent_id: str) -> dict:
        """Calculer les statistiques de beacons pour un agent"""
        docs = list(self.beacons.find({"agent_id": agent_id}).sort("created_at", ASCENDING))
        
        if not docs:
            return {
                "agent_id": agent_id,
                "total_beacons": 0,
                "first_beacon": None,
                "last_beacon": None,
                "avg_uptime_seconds": 0,
                "total_tasks_received": 0,
            }
        
        uptimes = [doc["uptime_seconds"] for doc in docs]
        tasks_count = sum(doc["tasks_count"] for doc in docs)
        
        return {
            "agent_id": agent_id,
            "total_beacons": len(docs),
            "first_beacon": docs[0]["created_at"].isoformat(),
            "last_beacon": docs[-1]["created_at"].isoformat(),
            "avg_uptime_seconds": int(sum(uptimes) / len(uptimes)) if uptimes else 0,
            "total_tasks_received": tasks_count,
        }
    
    # ===== UTILITAIRES =====
    
    def get_stats(self) -> dict:
        """RÃ©cupÃ©rer les statistiques globales"""
        return {
            "agents_count": self.agents.count_documents({}),
            "tasks_count": self.tasks.count_documents({}),
            "results_count": self.results.count_documents({}),
            "beacons_count": self.beacons.count_documents({}),
        }
    
    def clear_all(self):
        """âš ï¸ Vider toutes les collections (DANGER!)"""
        logger.warning("âš ï¸ Suppression de TOUTES les collections MongoDB!")
        self.agents.drop()
        self.tasks.drop()
        self.results.drop()
        self.beacons.drop()
        logger.warning("âœ“ Toutes les collections supprimÃ©es")


# Instance globale
try:
    if db is not None:
        db_instance = MongoDatabase()
        logger.info("âœ“ MongoDB activÃ© et prÃªt")
    else:
        db_instance = None
        logger.warning("MongoDB non disponible - Mode fallback")
except Exception as e:
    logger.error(f"Erreur initialisation MongoDB: {e}")
    db_instance = None

