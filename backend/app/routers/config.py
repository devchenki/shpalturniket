"""
Router для работы с конфигурационными данными
Интеграция с IP_list.json и config.json из оригинального приложения
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel

router = APIRouter()

# Пути к конфигурационным файлам
BASE_DIR = Path(__file__).parent.parent.parent
IP_LIST_PATH = BASE_DIR / "IP_list.json"
CONFIG_PATH = BASE_DIR / "config.json"

def _determine_category(device_id: str, description: str) -> str:
    """Определяет категорию устройства - все устройства турникеты"""
    return "Турникет"

class DeviceConfig(BaseModel):
    """Модель конфигурации устройства"""
    device_id: str
    ip: str
    description: str
    category: str
    enabled: bool

class BotConfig(BaseModel):
    """Модель конфигурации бота"""
    token: str
    time_connect: int
    chat_ids: List[int]

class ConfigResponse(BaseModel):
    """Ответ с конфигурационными данными"""
    devices: List[DeviceConfig]
    bot: BotConfig
    total_devices: int
    enabled_devices: int

# --- Internal functions to read/write config files ---
def _read_ip_list() -> Dict[str, List[str]]:
    if not IP_LIST_PATH.exists():
        return {}
    with open(IP_LIST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _read_main_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_main_config(config_data: Dict[str, Any]):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

# --- API Endpoints ---
@router.get("/config", response_model=ConfigResponse, summary="Get full application configuration")
async def get_full_config():
    devices = []
    ip_data = _read_ip_list()
    for device_id, device_info in ip_data.items():
        if len(device_info) >= 3:
            ip, description, enabled = device_info[0], device_info[1], bool(int(device_info[2]))
            category = _determine_category(device_id, description)
            devices.append(DeviceConfig(device_id=device_id, ip=ip, description=description, category=category, enabled=enabled))

    config_data = _read_main_config()
    bot_config = BotConfig(
        token=config_data.get("TOKEN", ""),
        time_connect=int(config_data.get("time_connect", 50)),
        chat_ids=config_data.get("chat_id", [])
    )

    total_devices = len(devices)
    enabled_devices = sum(1 for device in devices if device.enabled)

    return ConfigResponse(devices=devices, bot=bot_config, total_devices=total_devices, enabled_devices=enabled_devices)

@router.get("/config/devices", summary="Get device configuration")
async def get_devices_config():
    devices = []
    ip_data = _read_ip_list()
    for device_id, device_info in ip_data.items():
        if len(device_info) >= 3:
            ip, description, enabled = device_info[0], device_info[1], bool(int(device_info[2]))
            category = _determine_category(device_id, description)
            devices.append({"device_id": device_id, "ip": ip, "description": description, "category": category, "enabled": enabled})
    return {"devices": devices, "total": len(devices)}

@router.get("/config/bot", summary="Get Telegram bot configuration")
async def get_bot_config():
    config_data = _read_main_config()
    return {
        "token": config_data.get("TOKEN", ""),
        "time_connect": int(config_data.get("time_connect", 50)),
        "chat_ids": config_data.get("chat_id", []),
        "exists": bool(config_data.get("TOKEN"))
    }

@router.put("/config/bot", summary="Update Telegram bot configuration")
async def update_bot_config(new_config: BotConfig = Body(...)):
    config_data = _read_main_config()
    config_data["TOKEN"] = new_config.token
    config_data["time_connect"] = str(new_config.time_connect)
    config_data["chat_id"] = new_config.chat_ids
    _write_main_config(config_data)
    return {"message": "Bot configuration updated successfully", "success": True}

@router.get("/config/stats", summary="Get configuration statistics")
async def get_config_stats():
    devices = []
    ip_data = _read_ip_list()
    for device_id, device_info in ip_data.items():
        if len(device_info) >= 3:
            enabled = bool(int(device_info[2]))
            category = _determine_category(device_id, device_info[1])
            devices.append({"category": category, "enabled": enabled})

    category_stats = {}
    for device in devices:
        cat = device["category"]
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "enabled": 0}
        category_stats[cat]["total"] += 1
        if device["enabled"]:
            category_stats[cat]["enabled"] += 1

    total_devices = len(devices)
    enabled_devices = sum(1 for d in devices if d["enabled"])

    return {
        "total_devices": total_devices,
        "enabled_devices": enabled_devices,
        "disabled_devices": total_devices - enabled_devices,
        "categories": category_stats,
        "availability_percentage": round((enabled_devices / total_devices * 100) if total_devices > 0 else 0, 1)
    }
