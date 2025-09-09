"""
Router для проверки здоровья системы
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health", summary="Проверка здоровья системы")
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Shaplych Monitoring System"
    }
