#!/usr/bin/env python3
"""
Скрипт для миграции конфигурации устройств из IP_list.json в базу данных.
После выполнения этого скрипта система будет использовать БД как единственный источник истины.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.db import get_session
from app.models.device import Device
from sqlmodel import Session, select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_ip_list_json() -> dict:
    """Загрузить IP_list.json из корневой директории"""
    BASE_DIR = Path(__file__).parent.parent
    ip_list_path = BASE_DIR / "IP_list.json"
    
    if not ip_list_path.exists():
        logger.error(f"Файл {ip_list_path} не найден")
        return {}
    
    try:
        with open(ip_list_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения {ip_list_path}: {e}")
        return {}


def migrate_devices_to_db(dry_run: bool = False) -> tuple[int, int, int]:
    """
    Мигрировать устройства из JSON в БД.
    
    Returns:
        tuple: (created_count, updated_count, skipped_count)
    """
    ip_list_data = load_ip_list_json()
    
    if not ip_list_data:
        logger.warning("Нет данных для миграции")
        return (0, 0, 0)
    
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    with next(get_session()) as session:
        for device_id, device_info in ip_list_data.items():
            if not isinstance(device_info, list) or len(device_info) < 2:
                logger.warning(f"Некорректный формат данных для {device_id}, пропускаем")
                skipped_count += 1
                continue
            
            ip = device_info[0]
            description = device_info[1]
            
            # Третий элемент - флаг enabled (по умолчанию True если нет)
            enabled = True
            if len(device_info) >= 3:
                try:
                    enabled = bool(int(device_info[2]))
                except (ValueError, IndexError):
                    enabled = True
            
            # Проверяем существует ли устройство
            existing = session.exec(
                select(Device).where(Device.device_id == device_id)
            ).first()
            
            if existing:
                # Обновляем существующее
                old_ip = existing.ip
                old_desc = existing.description
                old_enabled = existing.enabled
                
                existing.ip = ip
                existing.description = description
                existing.enabled = enabled
                existing.updated_at = datetime.utcnow()
                
                changes = []
                if old_ip != ip:
                    changes.append(f"IP: {old_ip} → {ip}")
                if old_desc != description:
                    changes.append(f"Описание: {old_desc} → {description}")
                if old_enabled != enabled:
                    changes.append(f"Enabled: {old_enabled} → {enabled}")
                
                if changes:
                    logger.info(f"Обновление {device_id}: {', '.join(changes)}")
                    if not dry_run:
                        session.add(existing)
                    updated_count += 1
                else:
                    logger.debug(f"Устройство {device_id} не изменилось")
                    skipped_count += 1
            else:
                # Создаем новое
                device = Device(
                    device_id=device_id,
                    ip=ip,
                    description=description,
                    category="Турникет",
                    status="unknown",
                    enabled=enabled
                )
                logger.info(f"Создание {device_id}: IP={ip}, enabled={enabled}")
                if not dry_run:
                    session.add(device)
                created_count += 1
        
        if not dry_run:
            session.commit()
            logger.info("✅ Изменения сохранены в БД")
        else:
            logger.info("🔍 Dry-run режим: изменения НЕ сохранены")
    
    return (created_count, updated_count, skipped_count)


def verify_migration():
    """Проверить результаты миграции"""
    with next(get_session()) as session:
        devices = session.exec(select(Device)).all()
        
        logger.info(f"\n📊 Статистика БД:")
        logger.info(f"   Всего устройств: {len(devices)}")
        logger.info(f"   Включено: {sum(1 for d in devices if d.enabled)}")
        logger.info(f"   Выключено: {sum(1 for d in devices if not d.enabled)}")
        
        logger.info(f"\n📋 Список устройств:")
        for device in devices:
            status_icon = "✅" if device.enabled else "❌"
            logger.info(f"   {status_icon} {device.device_id}: {device.ip} - {device.description}")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Миграция конфигурации устройств из IP_list.json в БД'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Показать что будет сделано, но не применять изменения'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Проверить текущее состояние БД'
    )
    
    args = parser.parse_args()
    
    if args.verify:
        verify_migration()
        return 0
    
    logger.info("🚀 Начало миграции конфигурации устройств")
    logger.info(f"   Режим: {'DRY-RUN (без сохранения)' if args.dry_run else 'ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ'}")
    
    try:
        created, updated, skipped = migrate_devices_to_db(dry_run=args.dry_run)
        
        logger.info(f"\n📈 Результаты миграции:")
        logger.info(f"   Создано новых: {created}")
        logger.info(f"   Обновлено: {updated}")
        logger.info(f"   Пропущено: {skipped}")
        
        if not args.dry_run:
            logger.info("\n🎉 Миграция завершена успешно!")
            logger.info("\n💡 Следующие шаги:")
            logger.info("   1. Проверьте БД: python migrate_config_to_db.py --verify")
            logger.info("   2. Обновите MonitoringService для чтения из БД")
            logger.info("   3. После проверки можно удалить IP_list.json")
        else:
            logger.info("\n💡 Для применения изменений запустите без --dry-run")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
