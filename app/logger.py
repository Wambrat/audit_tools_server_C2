import logging
import logging.handlers
import json
from datetime import datetime
import os
from pathlib import Path
import re


class SecretsFilter(logging.Filter):
    """Filter to mask sensitive information in logs (passwords, tokens, API keys)"""
    
    # Patterns for sensitive data
    PATTERNS = [
        # JWT tokens (eyJ...)
        (r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED_JWT]'),
        # API keys and tokens in URLs or headers
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]+["\']?', 'api_key=[REDACTED]'),
        # Bearer tokens
        (r'Bearer\s+[A-Za-z0-9_.-]+', 'Bearer [REDACTED]'),
        # Password fields
        (r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'password=[REDACTED]'),
        # Database URLs with credentials
        (r'mongodb://[^:]+:[^@]+@', 'mongodb://[REDACTED]:[REDACTED]@'),
        # SQL connection strings
        (r'password=[^;]+', 'password=[REDACTED]'),
        # AWS keys
        (r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9/+=]+["\']?', 'aws_secret_access_key=[REDACTED]'),
        # Environment variables with secrets
        (r'ADMIN_PASSWORD["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ADMIN_PASSWORD=[REDACTED]'),
        (r'ADMIN_SECRET_KEY["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ADMIN_SECRET_KEY=[REDACTED]'),
        (r'ENCRYPTION_KEY["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ENCRYPTION_KEY=[REDACTED]'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive information from log records"""
        try:
            # Mask message
            if record.msg:
                msg_text = str(record.msg)
                for pattern, replacement in self.PATTERNS:
                    msg_text = re.sub(pattern, replacement, msg_text, flags=re.IGNORECASE)
                record.msg = msg_text

            # Mask args if present
            if record.args:
                if isinstance(record.args, dict):
                    sanitized_args = {}
                    for key, value in record.args.items():
                        sanitized_args[key] = re.sub(
                            r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]+["\']?',
                            'api_key=[REDACTED]',
                            str(value),
                            flags=re.IGNORECASE,
                        )
                    record.args = sanitized_args
                elif isinstance(record.args, tuple):
                    sanitized_args = []
                    for arg in record.args:
                        if isinstance(arg, str):
                            cleaned = arg
                            for pattern, replacement in self.PATTERNS:
                                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
                            sanitized_args.append(cleaned)
                        else:
                            sanitized_args.append(arg)
                    record.args = tuple(sanitized_args)
        except Exception:
            pass  # If filtering fails, still log the message

        return True


class JSONFormatter(logging.Formatter):
    """Formatteur personnalisé pour le logging en JSON"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Ajouter les informations d'exception si présentes
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Ajouter les champs personnalisés
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(app_name: str = "jadus-audit", log_level: str = None):
    """
    Configurer le logging structuré pour l'application.
    
    Args:
        app_name: Nom de l'application
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Déterminer le niveau de log
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Créer le répertoire logs s'il n'existe pas
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Créer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Create secrets filter
    secrets_filter = SecretsFilter()
    
    # Formatteur JSON
    json_formatter = JSONFormatter()
    
    # ===== Handler Console (développement) =====
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.addFilter(secrets_filter)
    
    # Formatteur simple pour la console (lisible)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # ===== Handler File (JSON) =====
    # Fichier global
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / f"{app_name}.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,  # Garder 10 fichiers de backup
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # Tout enregistrer dans le fichier
    file_handler.addFilter(secrets_filter)
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # ===== Handler File pour les erreurs (JSON) =====
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / f"{app_name}_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.addFilter(secrets_filter)
    error_file_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Récupérer un logger pour un module"""
    return logging.getLogger(name)


class StructuredLogger:
    """Wrapper pour logging structuré avec champs personnalisés"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def _log(self, level: int, message: str, **extra_fields):
        """Enregistrer un message avec champs personnalisés"""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)
    
    def debug(self, message: str, **extra):
        self._log(logging.DEBUG, message, **extra)
    
    def info(self, message: str, **extra):
        self._log(logging.INFO, message, **extra)
    
    def warning(self, message: str, **extra):
        self._log(logging.WARNING, message, **extra)
    
    def error(self, message: str, **extra):
        self._log(logging.ERROR, message, **extra)
    
    def critical(self, message: str, **extra):
        self._log(logging.CRITICAL, message, **extra)
