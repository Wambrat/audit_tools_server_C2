"""
Global Database Instance Manager

Cette couche permet au code d'accéder à l'instance de la base de données
sans créer de dépendance circulaire.

Utilisation:
    from app.db import get_db
    db = get_db()
"""

# Variable globale qui sera définie dans main.py
_db_instance = None


def set_db_instance(db):
    """Définir l'instance de la base de données (appelé par main.py)"""
    global _db_instance
    _db_instance = db


def get_db():
    """Obtenir l'instance de la base de données"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database instance not initialized. Call set_db_instance first.")
    return _db_instance
