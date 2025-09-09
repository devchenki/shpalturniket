"""
Модель устройства для мониторинга
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Device(SQLModel, table=True):
    """Устройство для мониторинга"""

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(index=True, max_length=50, unique=True)
    ip: str = Field(max_length=45, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    category: str = Field(default="Турникет", max_length=50, index=True)
    status: str = Field(default="unknown", max_length=20, index=True)
    response_ms: Optional[int] = Field(default=None)
    last_check: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceCreate(SQLModel):
    """Модель создания устройства"""

    device_id: str
    ip: str
    description: Optional[str] = None
    category: str = "Турникет"


class DeviceUpdate(SQLModel):
    """Модель обновления устройства"""

    ip: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    response_ms: Optional[int] = None
    last_check: Optional[datetime] = None

