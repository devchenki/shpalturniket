"""
Router для управления Telegram ботом
Интеграция с advanced_bot.py
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

# Путь к advanced_bot.py
BASE_DIR = Path(__file__).parent.parent.parent.parent
BOT_SCRIPT_PATH = BASE_DIR / "advanced_bot.py"

class BotStatus(BaseModel):
    """Статус бота"""
    is_running: bool
    pid: Optional[int] = None
    last_start: Optional[str] = None
    last_stop: Optional[str] = None
    error: Optional[str] = None

class BotConfig(BaseModel):
    """Конфигурация бота"""
    token: str
    time_connect: int
    chat_ids: list

# Глобальное состояние бота
bot_process: Optional[subprocess.Popen] = None
bot_status = BotStatus(is_running=False)

def _read_bot_config() -> Dict[str, Any]:
    """Читает конфигурацию бота из config.json"""
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_bot_config(config_data: Dict[str, Any]):
    """Записывает конфигурацию бота в config.json"""
    config_path = BASE_DIR / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

@router.get("/status", response_model=BotStatus, summary="Получить статус Telegram бота")
async def get_bot_status():
    """Получить текущий статус бота"""
    global bot_process, bot_status
    
    # Проверяем, запущен ли процесс
    if bot_process and bot_process.poll() is None:
        bot_status.is_running = True
        bot_status.pid = bot_process.pid
    else:
        bot_status.is_running = False
        bot_status.pid = None
        if bot_process:
            bot_status.last_stop = "Процесс завершен"
    
    return bot_status

@router.post("/start", summary="Запустить Telegram бота")
async def start_bot(background_tasks: BackgroundTasks):
    """Запустить Telegram бота"""
    global bot_process, bot_status
    
    if bot_status.is_running:
        raise HTTPException(status_code=400, detail="Бот уже запущен")
    
    try:
        # Проверяем наличие файла бота
        if not BOT_SCRIPT_PATH.exists():
            raise HTTPException(status_code=404, detail="Файл advanced_bot.py не найден")
        
        # Запускаем бота в фоновом режиме
        # Запускаем без перенаправления stdout/stderr, чтобы избежать блокировок буфера
        bot_process = subprocess.Popen(
            [sys.executable, str(BOT_SCRIPT_PATH)],
            cwd=str(BASE_DIR),
            env={**os.environ, 'PYTHONPATH': str(BASE_DIR)}
        )
        
        bot_status.is_running = True
        bot_status.pid = bot_process.pid
        bot_status.last_start = "Бот запущен"
        bot_status.error = None
        
        return {"message": "Telegram бот запущен успешно", "pid": bot_process.pid}
        
    except Exception as e:
        bot_status.error = str(e)
        raise HTTPException(status_code=500, detail=f"Ошибка запуска бота: {e}")

@router.post("/stop", summary="Остановить Telegram бота")
async def stop_bot():
    """Остановить Telegram бота"""
    global bot_process, bot_status
    
    if not bot_status.is_running or not bot_process:
        raise HTTPException(status_code=400, detail="Бот не запущен")
    
    try:
        # Завершаем процесс
        bot_process.terminate()
        
        # Ждем завершения
        try:
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
            bot_process.wait()
        
        bot_status.is_running = False
        bot_status.pid = None
        bot_status.last_stop = "Бот остановлен"
        bot_status.error = None
        
        return {"message": "Telegram бот остановлен успешно"}
        
    except Exception as e:
        bot_status.error = str(e)
        raise HTTPException(status_code=500, detail=f"Ошибка остановки бота: {e}")

@router.get("/config", response_model=BotConfig, summary="Получить конфигурацию бота")
async def get_bot_config():
    """Получить конфигурацию бота"""
    config_data = _read_bot_config()
    
    return BotConfig(
        token=config_data.get("TOKEN", ""),
        time_connect=int(config_data.get("time_connect", 50)),
        chat_ids=config_data.get("chat_id", [])
    )

@router.put("/config", summary="Обновить конфигурацию бота")
async def update_bot_config(config: BotConfig):
    """Обновить конфигурацию бота"""
    try:
        config_data = _read_bot_config()
        config_data["TOKEN"] = config.token
        config_data["time_connect"] = str(config.time_connect)
        config_data["chat_id"] = config.chat_ids
        
        _write_bot_config(config_data)
        
        return {"message": "Конфигурация бота обновлена успешно"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления конфигурации: {e}")

@router.get("/logs", summary="Получить логи бота")
async def get_bot_logs():
    """Получить логи бота"""
    try:
        logs = []
        
        # Читаем логи из файла, если он существует
        log_file_path = BASE_DIR / "bot.log"
        if log_file_path.exists():
            with open(log_file_path, 'r', encoding='utf-8') as f:
                # Читаем последние 100 строк
                all_lines = f.readlines()
                logs = [line.strip() for line in all_lines[-100:] if line.strip()]
        
        # Если файла нет — возвращаем пусто
        
        return {"logs": logs, "message": "Логи получены", "success": True}
        
    except Exception as e:
        return {"logs": [], "error": str(e), "success": False}


@router.delete("/logs", summary="Очистить логи бота")
async def clear_bot_logs():
    """Очистить файл логов бота"""
    try:
        log_file_path = BASE_DIR / "bot.log"
        if log_file_path.exists():
            # Обрезаем файл до нуля
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.truncate(0)
        return {"success": True, "message": "Логи очищены"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка очистки логов: {e}")

@router.post("/restart", summary="Перезапустить Telegram бота")
async def restart_bot(background_tasks: BackgroundTasks):
    """Перезапустить Telegram бота"""
    if bot_status.is_running:
        await stop_bot()
    
    await start_bot(background_tasks)
    return {"message": "Telegram бот перезапущен успешно"}
