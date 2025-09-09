"""
Router для ping операций
"""

import asyncio
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from icmplib import ping as icmp_ping

from ..core.db import get_session
from ..models.device import Device
from ..utils.events_bus import event_manager


router = APIRouter()


async def _ping_ip(ip_address: str, count: int = 1, timeout: int = 2):
    try:
        # icmplib.ping является синхронной функцией; оборачиваем в тред-пул
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, lambda: icmp_ping(ip_address, count=count, timeout=timeout))
        is_alive = getattr(result, 'is_alive', False)
        avg_rtt = getattr(result, 'avg_rtt', None)
        return {
            "alive": is_alive,
            "avg_ms": int(avg_rtt * 1000) if (avg_rtt is not None) else None,
        }
    except Exception:
        return {"alive": False, "avg_ms": None}


@router.post("/ping/all", response_model=List[dict], summary="Выполнить ping всех устройств из конфигурации")
async def ping_all_devices(session: Session = Depends(get_session)):
    # Загружаем список устройств из IP_list.json, чтобы соответствовать фронтенду
    from pathlib import Path
    import json

    BASE_DIR = Path(__file__).parent.parent.parent
    ip_list_path = BASE_DIR / "IP_list.json"

    ip_entries = {}
    if ip_list_path.exists():
        try:
            with open(ip_list_path, 'r', encoding='utf-8') as f:
                ip_entries = json.load(f)
        except Exception:
            ip_entries = {}

    # Преобразуем в список (device_id, ip)
    config_devices = []
    for dev_id, arr in ip_entries.items():
        if isinstance(arr, list) and len(arr) >= 1:
            config_devices.append((dev_id, arr[0]))

    # Если конфиг пуст, падаем назад на БД
    if not config_devices:
        db_devices: List[Device] = session.exec(select(Device)).all()
        config_devices = [(d.device_id, d.ip) for d in db_devices]

    tasks = [_ping_ip(ip) for _, ip in config_devices]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    now_iso = datetime.utcnow().isoformat()
    responses = []

    # Обновляем БД при наличии записи, но не требуем
    for (dev_id, ip), res in zip(config_devices, results):
        db_device: Device | None = session.exec(select(Device).where(Device.device_id == dev_id)).first()
        if db_device:
            db_device.status = "online" if res["alive"] else "offline"
            db_device.response_ms = res["avg_ms"]
            db_device.last_check = datetime.utcnow()
            session.add(db_device)

        payload = {
            "device_id": dev_id,
            "ip": ip,
            "status": "online" if res["alive"] else "offline",
            "response_time": res["avg_ms"],
            "timestamp": now_iso,
        }
        responses.append(payload)
        # Публикуем событие в SSE
        await event_manager.publish({
            "type": "device_status",
            "timestamp": now_iso,
            "data": payload,
        })
    session.commit()
    return responses


@router.get("/ping/device/{device_key}", summary="Пинг устройства по числовому ID или по device_id")
async def ping_device(device_key: str, session: Session = Depends(get_session)):
    device: Device | None = None

    # Попытка как числовой первичный ключ
    if device_key.isdigit():
        device = session.get(Device, int(device_key))
    # Если не найдено, ищем по device_id
    if not device:
        device = session.exec(select(Device).where(Device.device_id == device_key)).first()

    if device:
        res = await _ping_ip(device.ip)
        device.status = "online" if res["alive"] else "offline"
        device.response_ms = res["avg_ms"]
        device.last_check = datetime.utcnow()
        session.add(device)
        session.commit()
        payload = {
            "device_id": device.device_id,
            "ip": device.ip,
            "status": device.status,
            "response_time": device.response_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await event_manager.publish({
            "type": "device_status",
            "timestamp": payload["timestamp"],
            "data": payload,
        })
        return payload

    # Фоллбек: ищем IP в конфигурации
    from pathlib import Path
    import json
    BASE_DIR = Path(__file__).parent.parent.parent
    ip_list_path = BASE_DIR / "IP_list.json"
    if ip_list_path.exists():
        try:
            with open(ip_list_path, 'r', encoding='utf-8') as f:
                ip_entries = json.load(f)
            if device_key in ip_entries and isinstance(ip_entries[device_key], list) and len(ip_entries[device_key]) >= 1:
                ip = ip_entries[device_key][0]
                res = await _ping_ip(ip)
                payload = {
                    "device_id": device_key,
                    "ip": ip,
                    "status": "online" if res["alive"] else "offline",
                    "response_time": res["avg_ms"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await event_manager.publish({
                    "type": "device_status",
                    "timestamp": payload["timestamp"],
                    "data": payload,
                })
                return payload
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Устройство не найдено")


@router.get("/ping/ip/{ip}", summary="Пинг по IP адресу")
async def ping_ip(ip: str):
    res = await _ping_ip(ip)
    return {
        "device_id": ip,
        "ip": ip,
        "status": "online" if res["alive"] else "offline",
        "response_time": res["avg_ms"],
        "timestamp": datetime.utcnow().isoformat(),
    }
