import json
import re
from typing import List, Optional, Dict
from datetime import datetime
import uuid
from .models import Agent, Task, AuditResult, BeaconHistory, TaskStatus, AgentStatus, AuditTemplate, PowerShellCommandDefinition
from .logger import get_logger
from .encryption import get_encryptor, EncryptionError

logger = get_logger(__name__)


class Database:
    """
    Stockage en mémoire pour une v1.
    En production, remplacer par SQLAlchemy + PostgreSQL/MySQL
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, AuditResult] = {}
        self.beacon_history: Dict[str, BeaconHistory] = {}
        self.audit_templates: Dict[str, AuditTemplate] = {}
        self.powershell_commands: Dict[str, PowerShellCommandDefinition] = {}
        self.template_history: List[Dict] = []

    @staticmethod
    def _normalize_command_name(command_name: str) -> str:
        """Normaliser le nom d'une commande pour la déduplication."""
        return str(command_name or '').strip()

    @staticmethod
    def _ensure_script_invokes_function(script: str) -> str:
        """Ajoute un appel final à la fonction définie dans un script PowerShell pour éviter les sorties vides."""
        if not script or not str(script).strip():
            return script or ""

        content = script.rstrip()
        match = re.search(r'(?m)^\s*function\s+([A-Za-z0-9_-]+)\s*(?:\{|\()', content)
        if not match:
            return content

        function_name = match.group(1)
        call_pattern = rf'(?m)^\s*(?:&\s*)?{re.escape(function_name)}\s*(?:\(|$)'
        if re.search(call_pattern, content):
            return content

        if not content.endswith('\n'):
            content += '\n'
        content += f'\n{function_name}\n'
        return content

    def _get_valid_command_names(self) -> set[str]:
        """Renvoie les commandes autorisées: builtins + commandes custom enregistrées."""
        builtins = {
            "Get-Process", "Get-Service", "Get-AuditPolicy", "Get-LocalUser",
            "Get-LocalGroup", "Get-IPConfig", "Get-EventLog", "SystemInfo",
            "Get-NetAdapter", "Get-ChildItem", "Get-ComputerInfo"
        }
        custom_names = {command.name for command in self.powershell_commands.values() if command.enabled}
        return builtins | custom_names

    def create_powershell_command(self, name: str, description: str = "", script: str = "", created_by: str = "admin") -> PowerShellCommandDefinition:
        """Créer une commande PowerShell réutilisable dans les templates."""
        normalized_name = self._normalize_command_name(name)
        if not normalized_name:
            raise ValueError("Le nom de la commande est obligatoire")
        if not script or not str(script).strip():
            raise ValueError("Le script PowerShell ne peut pas être vide")

        existing = next((cmd for cmd in self.powershell_commands.values() if cmd.name.lower() == normalized_name.lower()), None)
        if existing:
            raise ValueError(f"Une commande nommée '{normalized_name}' existe déjà")

        command = PowerShellCommandDefinition(
            command_id=str(uuid.uuid4()),
            name=normalized_name,
            description=(description or '').strip(),
            script=str(script).strip(),
            created_by=(created_by or 'admin').strip() or 'admin',
            created_at=datetime.now(),
            enabled=True,
        )
        self.powershell_commands[command.command_id] = command
        logger.info(f"PowerShell command created: {command.name} ({command.command_id})")
        return command

    def list_powershell_commands(self) -> List[PowerShellCommandDefinition]:
        """Lister les commandes PowerShell enregistrées."""
        return list(self.powershell_commands.values())

    def get_powershell_command(self, command_id: str) -> Optional[PowerShellCommandDefinition]:
        """Récupérer une commande PowerShell par son identifiant."""
        return self.powershell_commands.get(command_id)

    def update_powershell_command(self, command_id: str, name: str, description: str = "", script: str = "", created_by: str = "admin") -> PowerShellCommandDefinition:
        """Mettre à jour une commande PowerShell existante."""
        command = self.get_powershell_command(command_id)
        if not command:
            raise ValueError("Commande PowerShell introuvable")

        normalized_name = self._normalize_command_name(name)
        if not normalized_name:
            raise ValueError("Le nom de la commande est obligatoire")
        if not script or not str(script).strip():
            raise ValueError("Le script PowerShell ne peut pas être vide")

        duplicate = next((cmd for cmd in self.powershell_commands.values() if cmd.command_id != command_id and cmd.name.lower() == normalized_name.lower()), None)
        if duplicate:
            raise ValueError(f"Une commande nommée '{normalized_name}' existe déjà")

        command.name = normalized_name
        command.description = (description or '').strip()
        command.script = str(script).strip()
        command.created_by = (created_by or command.created_by).strip() or command.created_by
        command.enabled = True

        self.powershell_commands[command_id] = command
        logger.info(f"PowerShell command updated: {command.name} ({command.command_id})")
        return command

    def delete_powershell_command(self, command_id: str) -> bool:
        """Supprimer une commande PowerShell enregistrée."""
        if command_id in self.powershell_commands:
            del self.powershell_commands[command_id]
            return True
        return False

    def get_powershell_command_by_name(self, command_name: str) -> Optional[PowerShellCommandDefinition]:
        """Récupère une commande PowerShell par son nom exact."""
        normalized = self._normalize_command_name(command_name)
        if not normalized:
            return None
        for command in self.powershell_commands.values():
            if command.name.lower() == normalized.lower():
                return command
        return None
    
    # ===== Agents =====
    
    def create_agent(self, agent_name: str, os_version: str, hostname: str, username: str) -> Agent:
        """Créer et enregistrer un nouvel agent"""
        agent_id = str(uuid.uuid4())
        api_key = str(uuid.uuid4())
        
        agent = Agent(
            agent_id=agent_id,
            api_key=api_key,
            agent_name=agent_name,
            os_version=os_version,
            hostname=hostname,
            username=username,
            created_at=datetime.now(),
            status=AgentStatus.ACTIVE
        )
        
        self.agents[agent_id] = agent
        logger.debug(f"Agent {agent_id} ({agent_name}) created in database")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Récupérer un agent par son ID"""
        return self.agents.get(agent_id)
    
    def authenticate_agent(self, agent_id: str, api_key: str) -> bool:
        """Valider les credentials de l'agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        return agent.api_key == api_key
    
    def update_agent_beacon(self, agent_id: str):
        """Mettre à jour le timestamp du dernier beacon et marquer comme actif"""
        agent = self.get_agent(agent_id)
        if agent:
            agent.last_beacon = datetime.now()
            agent.status = AgentStatus.ACTIVE  # Marquer l'agent comme actif
    
    def list_agents(self) -> List[Agent]:
        """Lister tous les agents"""
        return list(self.agents.values())
    
    def delete_agent(self, agent_id: str) -> bool:
        """Supprimer un agent et toutes ses tâches et résultats associés"""
        if agent_id not in self.agents:
            return False
        
        # Supprimer l'agent
        del self.agents[agent_id]
        
        # Supprimer toutes ses tâches
        task_ids_to_delete = [
            task_id for task_id, task in self.tasks.items()
            if task.agent_id == agent_id
        ]
        for task_id in task_ids_to_delete:
            del self.tasks[task_id]
        
        # Supprimer tous ses résultats
        result_ids_to_delete = [
            result_id for result_id, result in self.results.items()
            if result.agent_id == agent_id
        ]
        for result_id in result_ids_to_delete:
            del self.results[result_id]
        
        # Supprimer l'historique des beacons
        beacon_ids_to_delete = [
            beacon_id for beacon_id, beacon in self.beacon_history.items()
            if beacon.agent_id == agent_id
        ]
        for beacon_id in beacon_ids_to_delete:
            del self.beacon_history[beacon_id]
        
        logger.info(f"Agent {agent_id} deleted with all associated data")
        return True
    
    # ===== Tasks =====

    def _normalize_task_parameters(self, parameters: Optional[dict]) -> Optional[dict]:
        """Normaliser les paramètres d'une tâche pour qu'ils restent JSON-friendly et cohérents."""
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
    
    def _attach_command_script_to_parameters(self, command_name: str, parameters: Optional[dict]) -> Optional[dict]:
        """Ajoute le script PowerShell enregistré à la charge utile d'une tâche lorsque la commande existe."""
        normalized_parameters = self._normalize_task_parameters(parameters)
        if not normalized_parameters:
            normalized_parameters = {}

        command_def = self.get_powershell_command_by_name(command_name)
        if command_def and command_def.script and str(command_def.script).strip():
            normalized_parameters.setdefault("script", command_def.script)
            normalized_parameters.setdefault("script_body", command_def.script)
            normalized_parameters.setdefault("command_name", command_name)

        return normalized_parameters

    def create_task(self, agent_id: str, command: str, parameters: Optional[dict] = None, 
                   priority: int = 0, timeout_seconds: int = 300) -> Task:
        """Créer une nouvelle tâche pour un agent"""
        task_id = str(uuid.uuid4())
        normalized_parameters = self._attach_command_script_to_parameters(command, parameters)
        
        task = Task(
            task_id=task_id,
            agent_id=agent_id,
            command=command,
            parameters=normalized_parameters,
            priority=priority,
            status=TaskStatus.PENDING,
            timeout_seconds=timeout_seconds,
            created_at=datetime.now()
        )
        
        logger.debug(
            f"Task created: task_id={task_id}, agent_id={agent_id}, command={command}, priority={priority}"
        )
        self.tasks[task_id] = task
        return task
    
    def get_pending_tasks(self, agent_id: str) -> List[Task]:
        """Récupérer les tâches en attente pour un agent"""
        agent_tasks = [
            task for task in self.tasks.values()
            if task.agent_id == agent_id and task.status == TaskStatus.PENDING
        ]
        # Trier par priorité puis par date de création
        return sorted(agent_tasks, key=lambda t: (-t.priority, t.created_at))
    
    def mark_task_assigned(self, task_id: str):
        """Marquer une tâche comme assignée"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.ASSIGNED
            self.tasks[task_id].assigned_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Récupérer une tâche par son ID"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, agent_id: Optional[str] = None) -> List[Task]:
        """Lister les tâches, optionnellement filtrées par agent"""
        if agent_id:
            return [t for t in self.tasks.values() if t.agent_id == agent_id]
        return list(self.tasks.values())
    
    # ===== Results =====
    
    def store_result(self, task_id: str, agent_id: str, status: str, result: dict,
                    execution_time_ms: int, error_message: Optional[str] = None) -> AuditResult:
        """Enregistrer le résultat d'une tâche avec chiffrement
        
        Le résultat est chiffré avec AES-256-GCM avant stockage.
        Seul le hash et preview sont stockés en clair pour recherche/monitoring.
        """
        result_id = str(uuid.uuid4())
        
        # Convertir le résultat en string s'il est dict
        if isinstance(result, dict):
            result_str = json.dumps(result)
        else:
            result_str = str(result)
        
        try:
            # Chiffrer le résultat
            encryptor = get_encryptor()
            encrypted_result, nonce_hex = encryptor.encrypt(result_str)
            result_hash = encryptor.hash_result(result_str)
            result_preview = encryptor.generate_preview(result_str)
            
            # Créer l'audit result avec données chiffrées
            audit_result = AuditResult(
                result_id=result_id,
                task_id=task_id,
                agent_id=agent_id,
                status=status,
                result_encrypted=encrypted_result,  # Chiffré
                result_hash=result_hash,              # Hash pour recherche
                result_preview=result_preview,        # Preview pour UI
                result=result_str,                    # Plaintext (mémoire seulement)
                execution_time_ms=execution_time_ms,
                error_message=error_message,
                created_at=datetime.now()
            )
            
            self.results[result_id] = audit_result
            
            logger.info(
                f"Audit result stored: result_id={result_id}, task_id={task_id}, "
                f"agent_id={agent_id}, status={status}, hash={result_hash[:16]}..."
            )
            
            # Mettre à jour le statut de la tâche
            if task_id in self.tasks:
                if status == "success":
                    self.tasks[task_id].status = TaskStatus.COMPLETED
                else:
                    self.tasks[task_id].status = TaskStatus.FAILED
                self.tasks[task_id].completed_at = datetime.now()
            
            return audit_result
            
        except EncryptionError as e:
            logger.error(f"Failed to encrypt result: {str(e)}")
            raise
    
    def get_result(self, result_id: str) -> Optional[AuditResult]:
        """Récupérer un résultat par son ID et déchiffrer le contenu"""
        result = self.results.get(result_id)
        
        if result is None:
            return None
        
        try:
            # Déchiffrer le résultat si ce n'est pas déjà fait
            if result.result_encrypted and not result.result:
                encryptor = get_encryptor()
                result.result = encryptor.decrypt(result.result_encrypted)
                logger.debug(f"Decrypted result {result_id}")
        except EncryptionError as e:
            logger.error(f"Failed to decrypt result {result_id}: {str(e)}")
            # Retourner quand même, mais avec decryption_error dans les logs
        
        return result
    
    def get_results_by_task(self, task_id: str) -> List[AuditResult]:
        """Récupérer les résultats d'une tâche"""
        return [r for r in self.results.values() if r.task_id == task_id]
    
    def get_results_by_agent(self, agent_id: str) -> List[AuditResult]:
        """Récupérer tous les résultats d'un agent et déchiffrer le contenu"""
        results = [r for r in self.results.values() if r.agent_id == agent_id]
        
        try:
            encryptor = get_encryptor()
            for result in results:
                if result.result_encrypted and not result.result:
                    result.result = encryptor.decrypt(result.result_encrypted)
        except EncryptionError as e:
            logger.error(f"Failed to decrypt results for agent {agent_id}: {str(e)}")
        
        return results

    # ===== Audit Templates =====

    def create_audit_template(self, name: str, description: str, commands: List[str], created_by: str = "admin") -> AuditTemplate:
        """Créer une configuration d'audit contenant plusieurs commandes PowerShell"""
        cleaned_commands = []
        allowed_commands = self._get_valid_command_names()

        for command in commands:
            normalized = str(command).strip()
            if not normalized:
                continue
            if normalized not in allowed_commands:
                raise ValueError(f"Commande non autorisée: {normalized}")
            if normalized not in cleaned_commands:
                cleaned_commands.append(normalized)

        if not cleaned_commands:
            raise ValueError("La configuration d'audit doit contenir au moins une commande valide")

        template = AuditTemplate(
            template_id=str(uuid.uuid4()),
            name=name.strip(),
            description=description.strip(),
            commands=cleaned_commands,
            created_by=created_by.strip() or "admin",
            created_at=datetime.now(),
            enabled=True
        )

        self.audit_templates[template.template_id] = template
        logger.info(f"Audit template created: {template.template_id} ({template.name})")
        return template

    def list_audit_templates(self) -> List[AuditTemplate]:
        """Lister toutes les configurations d'audit"""
        return list(self.audit_templates.values())

    def get_audit_template(self, template_id: str) -> Optional[AuditTemplate]:
        """Récupérer une configuration d'audit"""
        return self.audit_templates.get(template_id)

    def update_audit_template(self, template_id: str, name: str, description: str, commands: List[str], created_by: str = "admin") -> AuditTemplate:
        """Mettre à jour une configuration d'audit existante"""
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
                raise ValueError(f"Commande non autorisée: {normalized}")
            if normalized not in cleaned_commands:
                cleaned_commands.append(normalized)

        if not cleaned_commands:
            raise ValueError("La configuration d'audit doit contenir au moins une commande valide")

        template.name = name.strip() or template.name
        template.description = description.strip() if description is not None else template.description
        template.commands = cleaned_commands
        template.created_by = (created_by or template.created_by).strip() or template.created_by
        template.enabled = True

        self.audit_templates[template.template_id] = template
        logger.info(f"Audit template updated: {template.template_id} ({template.name})")
        return template

    def duplicate_audit_template(self, template_id: str) -> AuditTemplate:
        """Dupliquer une configuration d'audit"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        duplicate = AuditTemplate(
            template_id=str(uuid.uuid4()),
            name=f"{template.name} (copie)",
            description=template.description,
            commands=list(template.commands),
            created_by=template.created_by,
            created_at=datetime.now(),
            enabled=template.enabled,
        )

        self.audit_templates[duplicate.template_id] = duplicate
        logger.info(f"Audit template duplicated: {template.template_id} -> {duplicate.template_id}")
        return duplicate

    def delete_audit_template(self, template_id: str) -> bool:
        """Supprimer une configuration d'audit"""
        if template_id in self.audit_templates:
            del self.audit_templates[template_id]
            return True
        return False

    def export_audit_template(self, template_id: str) -> Dict:
        """Exporter un template au format JSON-ready"""
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

    def record_template_application(self, template_id: str, agent_id: str, task_count: int = 0) -> Dict:
        """Historiser l'application d'un template à un agent"""
        entry = {
            "template_id": template_id,
            "agent_id": agent_id,
            "task_count": task_count,
            "applied_at": datetime.now().isoformat(),
        }
        self.template_history.insert(0, entry)
        return entry

    def get_template_history(self, limit: int = 50) -> List[Dict]:
        """Récupérer l'historique d'application des templates"""
        return self.template_history[:limit]

    def seed_default_modules(self, zip_path: Optional[str] = None) -> Dict[str, int]:
        """Importer les modules PowerShell standards présents dans modules.zip et les enregistrer comme commandes/templates."""
        import os
        import zipfile

        if zip_path is None:
            zip_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "modules.zip")

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
                    script_content = self._ensure_script_invokes_function(script_content)

                    if command_name.startswith('Get-') or command_name.startswith('Test-') or command_name.startswith('Set-'):
                        try:
                            existing = self.get_powershell_command_by_name(command_name)
                            if existing is None:
                                self.create_powershell_command(
                                    name=command_name,
                                    description=f"Module importé depuis {relative_name}",
                                    script=script_content,
                                    created_by='system'
                                )
                                command_count += 1
                            elif existing.script != script_content:
                                existing.script = script_content
                                existing.description = f"Module importé depuis {relative_name}"
                                self.powershell_commands[existing.command_id] = existing
                        except ValueError:
                            continue

                if command_count > 0:
                    imported_commands = {cmd.name for cmd in self.list_powershell_commands()}
                    default_templates = {
                        "Audit Sécurité Réseau": [
                            "Get-FirewallAudit",
                            "Get-IPv6Status",
                            "Get-LLMNRState",
                            "Get-NetBiosInfo",
                            "Get-VPNStatus",
                            "Get-EventMonitor",
                            "Get-LogStatus"
                        ],
                        "Audit Comptes Locaux": [
                            "Get-LocalUserAudit",
                            "Get-GroupsAudit",
                            "Get-Privilege",
                            "Get-PolPassAudit",
                            "Get-ADPolPassAudit",
                            "Get-JEAAudit",
                            "Get-LAPSAudit",
                            "Get-SMBSharesAudit"
                        ],
                        "Audit Windows Hardening": [
                            "Get-UACAudit",
                            "Get-AppLockerState",
                            "Get-ASRStatus",
                            "Get-DeviceGuardStatus",
                            "Get-CredentialGuardStatus",
                            "Get-ExploitProtectionStatus",
                            "Get-PowerShellLanguageMode",
                            "Get-SRPState",
                            "Get-OptionalFeaturesAudit",
                            "Get-SmartAppControlStatus"
                        ],
                        "Audit Protection & BitLocker": [
                            "Get-BitLockerAudit",
                            "Get-ThirdPartyEncryptionIndicators",
                            "Get-LMHashStatus",
                            "Get-LsassProtectionStatus",
                            "Get-ServerAntivirusStatus",
                            "Get-UpdateInfo"
                        ]
                    }

                    for template_name, commands in default_templates.items():
                        commands_to_keep = [name for name in commands if name in imported_commands]
                        if not commands_to_keep:
                            continue
                        try:
                            self.create_audit_template(
                                name=template_name,
                                description=f"Template de référence pour l’audit {template_name.lower()}",
                                commands=commands_to_keep,
                                created_by='system'
                            )
                            template_count += 1
                        except ValueError:
                            continue

            logger.info(f"Modules importés: {command_count} commandes, {template_count} templates")
            return {"commands": command_count, "templates": template_count}
        except Exception as exc:
            logger.error(f"Erreur lors de l'import des modules par défaut: {exc}")
            return {"commands": 0, "templates": 0}

    def build_tasks_from_template(self, template_id: str, agent_id: str) -> List[Task]:
        """Transformer une configuration d'audit en plusieurs tâches pour un agent.

        Paramètres standardisés côté backend :
        {
          "execution_context": "template",
          "template_id": "...",
          "template_name": "Audit Sécurité Réseau",
          "command_name": "Get-FirewallAudit",
          "command_index": 1,
          "command_total": 7
        }
        """
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        created_tasks = []
        total_commands = len(template.commands)

        for index, command in enumerate(template.commands, start=1):
            task = self.create_task(
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
                timeout_seconds=300,
            )
            created_tasks.append(task)
        return created_tasks

    def apply_template_to_all_agents(self, template_id: str) -> Dict:
        """Appliquer un template à tous les agents enregistrés"""
        template = self.get_audit_template(template_id)
        if not template:
            raise ValueError("Template d'audit introuvable")

        agents = list(self.agents.values())
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
            "message": f"Template appliqué à {len(agents)} agent(s)"
        }


# ===== Beacon History =====

    def record_beacon(self, agent_id: str, beacon_status: str, uptime_seconds: int, 
                     tasks_count: int, ip_address: Optional[str] = None, 
                     user_agent: Optional[str] = None) -> BeaconHistory:
        """Enregistrer un beacon dans l'historique"""
        beacon_id = str(uuid.uuid4())
        
        beacon = BeaconHistory(
            beacon_id=beacon_id,
            agent_id=agent_id,
            beacon_status=beacon_status,
            uptime_seconds=uptime_seconds,
            ip_address=ip_address,
            user_agent=user_agent,
            tasks_count=tasks_count,
            created_at=datetime.now()
        )
        
        self.beacon_history[beacon_id] = beacon
        logger.debug(
            f"Beacon recorded: beacon_id={beacon_id}, agent_id={agent_id}, beacon_status={beacon_status}, uptime_seconds={uptime_seconds}, tasks_count={tasks_count}"
        )
        return beacon
    
    def get_beacon_history(self, agent_id: str, limit: int = 100) -> List[BeaconHistory]:
        """Récupérer l'historique des beacons d'un agent"""
        agent_beacons = [
            b for b in self.beacon_history.values()
            if b.agent_id == agent_id
        ]
        # Trier par date décroissante et limiter
        return sorted(agent_beacons, key=lambda b: b.created_at, reverse=True)[:limit]
    
    def get_beacon_history_range(self, agent_id: str, start_time: datetime, 
                                end_time: datetime) -> List[BeaconHistory]:
        """Récupérer l'historique des beacons dans une plage de temps"""
        return [
            b for b in self.beacon_history.values()
            if b.agent_id == agent_id and start_time <= b.created_at <= end_time
        ]
    
    def get_beacon_stats(self, agent_id: str) -> Dict:
        """Obtenir les statistiques de beacon pour un agent"""
        beacons = self.get_beacon_history(agent_id, limit=1000)
        
        if not beacons:
            return {
                "agent_id": agent_id,
                "total_beacons": 0,
                "first_beacon": None,
                "last_beacon": None,
                "avg_uptime_seconds": 0
            }
        
        total_uptime = sum(b.uptime_seconds for b in beacons)
        avg_uptime = total_uptime / len(beacons) if beacons else 0
        
        return {
            "agent_id": agent_id,
            "total_beacons": len(beacons),
            "first_beacon": min(beacons, key=lambda b: b.created_at).created_at,
            "last_beacon": beacons[0].created_at,  # Déjà trié par date décroissante
            "avg_uptime_seconds": int(avg_uptime),
            "total_tasks_received": sum(b.tasks_count for b in beacons)
        }
        return [r for r in self.results.values() if r.agent_id == agent_id]


# Instance globale de la base de données
db = Database()
