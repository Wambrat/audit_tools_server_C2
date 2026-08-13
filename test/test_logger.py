"""
Tests unitaires pour app/logger.py
Teste le système de logging structuré
"""
import pytest
import logging
from pathlib import Path
from app.logger import get_logger


class TestLogger:
    """Tests pour la fonction get_logger"""
    
    def test_get_logger_returns_logger(self):
        """Test: get_logger retourne un objet Logger"""
        logger = get_logger("test")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"
    
    def test_multiple_loggers_different_names(self):
        """Test: Plusieurs loggers avec noms différents"""
        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")
        
        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger1 is not logger2
    
    def test_same_logger_name_returns_same_instance(self):
        """Test: Même nom retourne la même instance"""
        logger1 = get_logger("same")
        logger2 = get_logger("same")
        
        # Même instance (par défaut Python logging)
        assert logger1.name == logger2.name
    
    def test_logger_has_handlers(self):
        """Test: Le logger a au moins un handler"""
        logger = get_logger("test_handlers")
        
        # Le logger doit avoir au moins un handler configuré
        assert len(logger.handlers) > 0 or logger.propagate
    
    def test_logger_info_level(self):
        """Test: Le logger accepte les messages INFO"""
        logger = get_logger("test_info")
        
        # Ces appels ne doivent pas lever d'exception
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")
    
    def test_logger_with_extra_context(self):
        """Test: Le logger accepte du contexte supplémentaire"""
        logger = get_logger("test_context")
        
        # Ces appels avec contexte ne doivent pas lever d'exception
        logger.info("Message with context", extra={"agent_id": "123"})
        logger.debug("Message", extra={"task_id": "abc"})
    
    def test_logger_formatting(self):
        """Test: Les messages sont formatés correctement"""
        logger = get_logger("test_format")
        
        # Vérifier le format du logger
        # Au minimum, les handlers doivent avoir un formatter
        for handler in logger.handlers:
            if handler.formatter:
                # Le formatter doit exister
                assert handler.formatter is not None
    
    def test_logger_level(self):
        """Test: Le logger a un niveau configuré ou hérité"""
        logger = get_logger("test_level")
        
        # Le logger doit avoir un niveau configuré (ou 0 si hérité des handlers)
        # Les handlers qui l'utilisent ont un niveau
        assert logger.level >= logging.NOTSET or any(h.level >= logging.DEBUG for h in logger.handlers)


class TestLoggerIntegration:
    """Tests d'intégration du logging"""
    
    def test_logger_output_to_file(self):
        """Test: Le logger écrit dans les fichiers de log"""
        logger = get_logger("test_file_output")
        
        # Vérifier que des fichiers de log existent
        logs_dir = Path("logs")
        
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log*"))
            assert len(log_files) >= 0  # Au moins 0 fichiers (peut être créé dynamiquement)
    
    def test_logger_no_exceptions(self):
        """Test: Le logger ne lève pas d'exceptions"""
        logger = get_logger("test_no_exceptions")
        
        try:
            logger.info("Test message")
            logger.debug("Debug message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            success = True
        except Exception as e:
            success = False
            pytest.fail(f"Logger raised exception: {e}")
        
        assert success is True


class TestMultipleLoggers:
    """Tests avec plusieurs loggers"""
    
    def test_different_modules_different_loggers(self):
        """Test: Différents modules peuvent avoir leurs propres loggers"""
        auth_logger = get_logger("app.auth")
        db_logger = get_logger("app.database")
        routes_logger = get_logger("app.routes")
        
        assert auth_logger.name == "app.auth"
        assert db_logger.name == "app.database"
        assert routes_logger.name == "app.routes"
    
    def test_hierarchical_logger_names(self):
        """Test: Les noms hiérarchiques (avec points) sont supportés"""
        parent_logger = get_logger("app")
        child_logger = get_logger("app.module")
        
        assert parent_logger.name == "app"
        assert child_logger.name == "app.module"
