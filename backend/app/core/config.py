"""
Конфигурация приложения
"""

import os
from typing import Dict, Any

def get_settings() -> Dict[str, Any]:
    """Получить настройки приложения"""
    return {
        "APP_NAME": "Shaplych Monitoring System",
        "VERSION": "1.0.0",
        "API_PREFIX": "/api",
        "PORT": os.getenv("PORT", "8771"),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
        "DB_PATH": os.getenv("DB_PATH", "shaplych_monitoring.db"),
        "DB_ECHO": os.getenv("DB_ECHO", "false").lower() == "true",
    }

settings = get_settings()
