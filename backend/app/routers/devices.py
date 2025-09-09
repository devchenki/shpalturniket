"""
Router для управления устройствами
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..core.db import get_session
from ..models.device import Device, DeviceCreate, DeviceUpdate


router = APIRouter()


@router.get("/devices/", response_model=List[Device], summary="Получить список устройств")
async def list_devices(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return devices


@router.post("/devices/", response_model=Device, status_code=201, summary="Создать устройство")
async def create_device(device_data: DeviceCreate, session: Session = Depends(get_session)):
    # Проверка уникальности device_id
    existing = session.exec(select(Device).where(Device.device_id == device_data.device_id)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Устройство с таким device_id уже существует")

    # Создаем устройство
    device = Device(
        device_id=device_data.device_id,
        ip=device_data.ip,
        description=device_data.description,
        category=device_data.category,
        status="unknown",
    )
    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@router.get("/devices/{device_id}", response_model=Device, summary="Получить устройство по ID записи")
async def get_device(device_id: int, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    return device


@router.put("/devices/{device_id}", response_model=Device, summary="Обновить устройство")
async def update_device(device_id: int, updates: DeviceUpdate, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
    device.updated_at = datetime.utcnow()

    session.add(device)
    session.commit()
    session.refresh(device)
    return device


@router.delete("/devices/{device_id}", status_code=204, summary="Удалить устройство")
async def delete_device(device_id: int, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    session.delete(device)
    session.commit()
    return None
