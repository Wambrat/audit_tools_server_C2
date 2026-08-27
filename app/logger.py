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
            if record.msg:
                msg_text = str(record.msg)
                for pattern, replacement in self.PATTERNS:
                    msg_text = re.sub(pattern, replacement, msg_text, flags=re.IGNORECASE)
                record.msg = msg_text

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
            pass

        return True


class JSONFormatter(logging.Formatter):
    """Formatter for structured JSON logs."""

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

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


def _normalize_service_name(name: str) -> str:
    """Retourne le service associé à un logger : api, db, web."""
    service_name = str(name or "api").lower().strip()

    if service_name in {"web", "website", "frontend", "panel", "ui", "dashboard"}:
        return "web"
    if any(token in service_name for token in ("db", "database", "mongo", "mongodb", "sql")):
        return "db"
    if any(token in service_name for token in ("web", "panel", "frontend", "ui", "dashboard")):
        return "web"
    return "api"


def _ensure_service_log_dir(service_name: str) -> Path:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    service_dir = log_dir / service_name
    service_dir.mkdir(exist_ok=True)
    return service_dir


def _attach_service_handlers(logger: logging.Logger, service_name: str, level: int):
    """Crée logs/<service>/info.log et logs/<service>/error.log."""
    service_dir = _ensure_service_log_dir(service_name)
    info_file = service_dir / "info.log"
    error_file = service_dir / "error.log"

    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    secrets_filter = SecretsFilter()
    json_formatter = JSONFormatter()

    info_handler = logging.handlers.RotatingFileHandler(
        filename=info_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(secrets_filter)
    info_handler.setFormatter(json_formatter)
    logger.addHandler(info_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(secrets_filter)
    error_handler.setFormatter(json_formatter)
    logger.addHandler(error_handler)


def setup_logging(app_name: str = "jadus-server", log_level: str = None, service_name: str = None):
    """
    Configure le logging structuré pour un service.
    Les logs sont stockés dans logs/<service>/info.log et error.log.
    Le service peut être explicite via l'argument service_name ou les variables
    JADUS_SERVICE_NAME / SERVICE_NAME / LOG_SERVICE_NAME.
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    resolved_service_name = (
        service_name or os.getenv("JADUS_SERVICE_NAME") or os.getenv("SERVICE_NAME") or os.getenv("LOG_SERVICE_NAME") or app_name
    )
    service_name = _normalize_service_name(resolved_service_name)
    log_level_value = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)

    if not any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
        for handler in root_logger.handlers
    ):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level_value)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        root_logger.addHandler(console_handler)

    service_logger = logging.getLogger(service_name)
    _attach_service_handlers(service_logger, service_name, log_level_value)
    return service_logger


def setup_web_logging(log_level: str = None):
    """Configure le logger dédié au service web dans logs/web/*.log."""
    return setup_logging(app_name="web", log_level=log_level, service_name="web")


def get_service_logger(service_name: str, log_level: str = None) -> logging.Logger:
    """Retourne un logger dédié à un service technique (api, db, web)."""
    return setup_logging(app_name=service_name, log_level=log_level, service_name=service_name)


def get_logger(name: str) -> logging.Logger:
    """Récupérer un logger pour un module, classé par service."""
    logger_name = str(name or "api")
    service_name = _normalize_service_name(logger_name)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.getLogger().getEffectiveLevel())
    logger.propagate = False

    if not logger.handlers:
        _attach_service_handlers(logger, service_name, logger.level)

    return logger


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
            None,
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
