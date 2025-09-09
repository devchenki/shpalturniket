"""
Модели для сценариев (на будущее/расширение)
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Scenario(SQLModel, table=True):
    """Сценарий мониторинга/уведомлений"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


