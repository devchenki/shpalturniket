"""
Модели для мероприятий
"""

from typing import List, Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class EventCategory(SQLModel, table=True):
    """Категория мероприятия"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EventDevice(SQLModel, table=True):
    """Связь устройства с мероприятием"""
    id: Optional[int] = Field(default=None, primary_key=True)
    event_category_id: int = Field(foreign_key="eventcategory.id")
    device_id: str = Field(max_length=50)
    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EventCategoryCreate(SQLModel):
    """Создание категории мероприятия"""
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

class EventCategoryUpdate(SQLModel):
    """Обновление категории мероприятия"""
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None

class EventDeviceUpdate(SQLModel):
    """Обновление устройства в мероприятии"""
    device_id: str
    is_enabled: bool

class EventCategoryWithDevices(SQLModel, table=False):
    """Категория мероприятия с устройствами (DTO-модель для ответов)"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    devices: List[EventDevice] = Field(default_factory=list)
    enabled_devices_count: int = 0
    total_devices_count: int = 0
