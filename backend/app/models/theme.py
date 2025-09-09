"""
Модели для пресетов тем оформления
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field


class ThemePreset(SQLModel, table=True):
    """Пресет темы приложения"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True, unique=True)
    palette: Optional[str] = Field(default=None, description="JSON строка с цветовой палитрой")
    components: Optional[str] = Field(default=None, description="JSON строка с настройками компонентов")
    created_at: datetime = Field(default_factory=datetime.utcnow)


