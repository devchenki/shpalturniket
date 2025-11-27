#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TurboShpalych Pro Bot - Modern Refactored Version
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Современная переработанная версия с улучшенной архитектурой, 
модульной структурой и повышенной отказоустойчивостью.
"""

import asyncio
import importlib
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

# Импортируем наши модули
from bot_ui_components import UIComponents, UIIcons
from bot_monitoring_service import DeviceInfo, CategoryInfo, MonitoringService
from bot_fsm_handlers import FSMHandlers, UserStates
from bot_error_handler import structured_logger, error_handler
from bot_shutdown_manager import shutdown_manager, ShutdownReason


class ModernTurboPingBot:
    """Современный переработанный TurboShpalych Pro бот"""
    
    def __init__(self):
        # Основные компоненты
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.storage: Optional[MemoryStorage] = None
        
        # Сервисы
        self.ping = None
        self.monitoring_service: Optional[MonitoringService] = None
        self.ui: Optional[UIComponents] = None
        self.fsm_handlers: Optional[FSMHandlers] = None
        
        # Данные
        self.devices: Dict[str, DeviceInfo] = {}
        self.categories: Dict[str, CategoryInfo] = {}
        self.time_connect: int = 50
        
        # Состояние
        self.is_running = False
        self.startup_time: Optional[datetime] = None
        
        # Инициализация
        self._initialize_components()
        self._setup_shutdown_tasks()
    
    def _initialize_components(self):
        """Инициализировать все компоненты бота"""
        try:
            # Загружаем модуль Ping
            import Ping
            importlib.reload(Ping)
            from Ping import Ping_IP
            self.ping = Ping_IP()
            structured_logger.log_structured(
                level='INFO',
                message="Ping module loaded successfully",
                category='system'
            )
            
            # Загружаем конфигурацию
            from Read_config import TOKEN, time_connect, chat_id, read_config
            self.bot_token = TOKEN
            self.time_connect = time_connect
            self.chat_ids = chat_id if isinstance(chat_id, list) else [chat_id]
            
            structured_logger.log_structured(
                level='INFO',
                message="Configuration loaded successfully",
                category='system',
                extra_data={
                    'time_connect': time_connect,
                    'chat_ids_count': len(self.chat_ids)
                }
            )
            
            # Инициализируем Telegram компоненты
            self.bot = Bot(token=self.bot_token)
            self.storage = MemoryStorage()
            self.dp = Dispatcher(storage=self.storage)
            
            # Инициализируем сервисы
            self.monitoring_service = MonitoringService(
                ping_instance=self.ping,
                cache_ttl=30.0
            )
            
            self.ui = UIComponents()
            self.fsm_handlers = FSMHandlers(self)
            
            # Загружаем данные устройств
            self._load_device_configuration()
            self._categorize_devices()
            
            # Регистрируем обработчики
            self.fsm_handlers.register_all_handlers(self.dp)
            
            # Устанавливаем callback для GUI логирования
            structured_logger.set_gui_callback(self.log_to_gui)
            
            structured_logger.log_structured(
                level='INFO',
                message=f"Bot initialized with {len(self.devices)} devices in {len(self.categories)} categories",
                category='system',
                extra_data={
                    'devices_count': len(self.devices),
                    'categories_count': len(self.categories)
                }
            )
            
        except Exception as e:
            structured_logger.log_structured(
                level='CRITICAL',
                message=f"Failed to initialize bot: {str(e)}",
                category='system',
                severity='critical',
                exception=e
            )
            raise
    
    def _setup_shutdown_tasks(self):
        """Настроить задачи для грациозного завершения"""
        # Задачи завершения с приоритетами
        shutdown_manager.register_task(
            name="stop_bot_polling",
            func=self._stop_bot_polling,
            priority=0,
            timeout=10.0,
            critical=True
        )
        
        shutdown_manager.register_task(
            name="send_shutdown_notification",
            func=self._send_shutdown_notification,
            priority=5,
            timeout=15.0,
            critical=False
        )
        
        shutdown_manager.register_task(
            name="cleanup_bot_session",
            func=self._cleanup_bot_session,
            priority=10,
            timeout=10.0,
            critical=True
        )
        
        shutdown_manager.register_task(
            name="log_final_statistics",
            func=self._log_final_statistics,
            priority=15,
            timeout=5.0,
            critical=False
        )
        
        # Коллбэки
        shutdown_manager.register_before_shutdown_callback(self._before_shutdown)
        shutdown_manager.register_after_shutdown_callback(self._after_shutdown)
    
    def _load_device_configuration(self):
        """Загрузить конфигурацию устройств"""
        try:
            from Read_config import read_config
            config_data = read_config()
            
            def _is_valid_ip(ip: str) -> bool:
                try:
                    parts = str(ip).split('.')
                    if len(parts) != 4:
                        return False
                    for p in parts:
                        v = int(p)
                        if v < 0 or v > 255:
                            return False
                    return True
                except Exception:
                    return False
            
            self.devices = {}
            for device_id, device_data in config_data.items():
                # Пропускаем служебные и некорректные
                if not device_id or not isinstance(device_data, (list, tuple)) or len(device_data) < 2:
                    continue
                
                ip = device_data[0]
                location = device_data[1]
                
                if not _is_valid_ip(ip):
                    continue
                
                category = device_id[0].upper() if device_id else 'OTHER'
                
                self.devices[device_id] = DeviceInfo(
                    id=device_id,
                    ip=str(ip),
                    location=str(location),
                    category=category
                )
            
            structured_logger.log_structured(
                level='INFO',
                message=f"Loaded {len(self.devices)} devices from configuration",
                category='system',
                extra_data={'devices_count': len(self.devices)}
            )
            
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error loading device configuration: {str(e)}",
                category='configuration',
                severity='high',
                exception=e
            )
            self.devices = {}
    
    def _categorize_devices(self):
        """Организовать устройства по категориям"""
        category_config = {
            'C': ('Central C', UIIcons.CENTRAL),
            'D': ('Passage D', UIIcons.PASSAGE),
            'E': ('Escalator E', UIIcons.ESCALATOR),
            'F': ('Transition F', UIIcons.TRANSITION),
            'G': ('Entrance G', UIIcons.ENTRANCE),
            'H': ('Hall H', UIIcons.HALL)
        }
        
        # Создаем категории
        for cat_id, (name, icon) in category_config.items():
            self.categories[cat_id] = CategoryInfo(
                id=cat_id,
                name=name,
                icon=icon
            )
        
        # Распределяем устройства по категориям
        for device in self.devices.values():
            if device.category in self.categories:
                self.categories[device.category].devices.append(device.id)
        
        # Удаляем пустые категории
        self.categories = {
            k: v for k, v in self.categories.items() 
            if v.devices
        }
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Organized devices into {len(self.categories)} categories",
            category='system',
            extra_data={'categories_count': len(self.categories)}
        )
    
    def _build_startup_summary_messages(self, devices: List[DeviceInfo]) -> List[str]:
        """Сформировать сообщения стартовой сводки"""
        try:
            stats = self.monitoring_service.get_statistics(devices)
            online = [d for d in devices if d.status == "онлайн"]
            offline = [d for d in devices if d.status == "офлайн"]
            
            header = (
                f"<b>{UIIcons.ROCKET} Startup Summary</b>\n\n"
                f"Total: {stats['total']} | {UIIcons.ONLINE} {stats['online']} | {UIIcons.OFFLINE} {stats['offline']}\n"
                f"{UIIcons.CLOCK} {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            
            parts = [header]
            
            # Формируем таблицы
            def build_table(title: str, items: List[DeviceInfo]) -> str:
                rows = [f"{d.id} — {d.ip}" for d in sorted(items, key=lambda x: x.id)]
                return f"<b>{title}</b>\n" + self.ui.format_two_columns(rows, col_width=30)
            
            if online:
                parts.append(build_table(f"{UIIcons.ONLINE} Online", online))
            
            if offline:
                parts.append(build_table(f"{UIIcons.OFFLINE} Offline", offline))
            
            # Разбиваем по лимиту Telegram
            messages = []
            current = ""
            
            for part in parts:
                if len(current) + len(part) + 2 > 3800:
                    messages.append(current)
                    current = part
                else:
                    current = (current + "\n\n" + part) if current else part
            
            if current:
                messages.append(current)
            
            return [msg for msg in messages if msg.strip()]
            
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error building startup summary: {str(e)}",
                category='system',
                exception=e
            )
            return []
    
    def log_to_gui(self, message: str):
        """Отправить сообщение в GUI через callback"""
        # Этот метод может быть переопределен для интеграции с GUI
        pass
    
    def get_alert_chats(self) -> List[int]:
        """Нормализовать chat_id из конфигурации в список int"""
        try:
            result = []
            for chat_id in self.chat_ids:
                try:
                    result.append(int(chat_id))
                except (ValueError, TypeError):
                    continue
            return result
        except Exception:
            return []
    
    async def send_alert_to_all_chats(self, message: str):
        """Отправить уведомление во все настроенные чаты"""
        try:
            alert_chats = self.get_alert_chats()
            
            for chat in alert_chats:
                try:
                    await self.bot.send_message(
                        chat_id=chat,
                        text=message,
                        parse_mode="HTML"
                    )
                    structured_logger.log_structured(
                        level='INFO',
                        message=f"Alert sent to chat {chat}",
                        category='telegram_api',
                        extra_data={'chat_id': chat}
                    )
                except Exception as e:
                    await error_handler.handle_telegram_error(
                        error=e,
                        message_or_callback=None,
                        context={'operation': 'send_alert', 'chat_id': chat}
                    )
                    
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error sending alerts: {str(e)}",
                category='telegram_api',
                exception=e
            )
    
    # ============= Методы жизненного цикла =============
    
    async def start(self):
        """Запустить бота"""
        if self.is_running:
            structured_logger.log_structured(
                level='WARNING',
                message="Bot is already running",
                category='system'
            )
            return
        
        self.is_running = True
        self.startup_time = datetime.now()
        
        structured_logger.log_structured(
            level='INFO',
            message="Starting modern TurboShpalych Pro bot...",
            category='system',
            extra_data={'startup_time': self.startup_time.isoformat()}
        )
        
        try:
            # Настраиваем обработчики сигналов
            shutdown_manager.setup_signal_handlers()
            
            # Отключаем вебхук для Long Polling
            await self._disable_webhook()
            
            # Устанавливаем команды бота
            await self._set_bot_commands()
            
            # Выполняем стартовую проверку устройств
            await self._perform_startup_checks()
            
            # Запускаем основной цикл
            await self._start_polling()
            
        except Exception as e:
            structured_logger.log_structured(
                level='CRITICAL',
                message=f"Bot startup failed: {str(e)}",
                category='system',
                severity='critical',
                exception=e
            )
            await shutdown_manager.initiate_shutdown(
                ShutdownReason.CRITICAL_ERROR,
                timeout=30.0
            )
        finally:
            # Гарантируем завершение работы
            if self.is_running:
                await shutdown_manager.initiate_shutdown(
                    ShutdownReason.SYSTEM_SHUTDOWN
                )
    
    async def _disable_webhook(self):
        """Отключить вебхук"""
        try:
            await self.bot.delete_webhook(drop_pending_updates=True)
            structured_logger.log_structured(
                level='INFO',
                message="Webhook disabled (switching to long polling)",
                category='telegram_api'
            )
        except Exception as e:
            await error_handler.handle_telegram_error(
                error=e,
                message_or_callback=None,
                context={'operation': 'disable_webhook'}
            )
    
    async def _set_bot_commands(self):
        """Установить команды бота"""
        try:
            await self.bot.set_my_commands([
                types.BotCommand(command="start", description="Open main menu"),
                types.BotCommand(command="help", description="Show help"),
                types.BotCommand(command="stats", description="Show statistics")
            ])
            
            structured_logger.log_structured(
                level='INFO',
                message="Telegram bot commands set successfully",
                category='telegram_api'
            )
            
        except Exception as e:
            await error_handler.handle_telegram_error(
                error=e,
                message_or_callback=None,
                context={'operation': 'set_bot_commands'}
            )
    
    async def _perform_startup_checks(self):
        """Выполнить стартовую проверку устройств"""
        try:
            devices_list = list(self.devices.values())
            
            if devices_list:
                checked_devices = await error_handler.execute_with_retry(
                    self.monitoring_service.check_multiple_devices,
                    devices_list,
                    use_cache=False,
                    force_refresh=True,
                    context={'operation': 'startup_checks'}
                )
                
                # Обновляем локальные статусы
                for device in checked_devices:
                    self.devices[device.id] = device
                
                # Отправляем стартовую сводку
                summary_messages = self._build_startup_summary_messages(checked_devices)
                for message in summary_messages:
                    await self.send_alert_to_all_chats(message)
                
                structured_logger.log_structured(
                    level='INFO',
                    message="Startup checks completed successfully",
                    category='system',
                    extra_data={
                        'devices_checked': len(checked_devices),
                        'summary_messages': len(summary_messages)
                    }
                )
            
        except Exception as e:
            structured_logger.log_structured(
                level='WARNING',
                message=f"Startup checks failed: {str(e)}",
                category='system',
                severity='medium',
                exception=e
            )
    
    async def _start_polling(self):
        """Запустить опрос"""
        structured_logger.log_structured(
            level='INFO',
            message="Telegram bot started and ready to work!",
            category='system'
        )
        
        structured_logger.log_structured(
            level='INFO',
            message="Send /start in Telegram to begin",
            category='system'
        )
        
        # Создаем задачу для опроса с поддержкой отмены
        polling_task = shutdown_manager.create_cancellation_aware_task(
            self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                drop_pending_updates=True
            ),
            name="bot_polling"
        )
        
        # Ожидаем завершения или запроса на остановку
        try:
            await shutdown_manager.wait_for_shutdown_request()
            
            structured_logger.log_structured(
                level='INFO',
                message="Shutdown request received, stopping polling...",
                category='system'
            )
            
            # Отменяем задачу опроса
            polling_task.cancel()
            
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error in polling loop: {str(e)}",
                category='system',
                exception=e
            )
    
    # ============= Задачи завершения =============
    
    async def _stop_bot_polling(self):
        """Остановить опрос бота"""
        if self.dp:
            structured_logger.log_structured(
                level='INFO',
                message="Stopping bot polling...",
                category='system'
            )
            # Остановка происходит в _start_polling
    
    async def _send_shutdown_notification(self):
        """Отправить уведомление о завершении"""
        try:
            uptime = None
            if self.startup_time:
                uptime = (datetime.now() - self.startup_time).total_seconds()
            
            message = f"""
{UIIcons.ROBOT} <b>Bot Shutdown</b>

{UIIcons.CLOCK} Shutdown time: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
{UIIcons.CLOCK} Uptime: {uptime:.1f}s if uptime else 'Unknown'
{UIIcons.DEVICE} Devices monitored: {len(self.devices)}

Bot will restart automatically.
"""
            
            await self.send_alert_to_all_chats(message)
            
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error sending shutdown notification: {str(e)}",
                category='telegram_api',
                exception=e
            )
    
    async def _cleanup_bot_session(self):
        """Очистить сессию бота"""
        try:
            if self.bot and self.bot.session:
                await self.bot.session.close()
                structured_logger.log_structured(
                    level='INFO',
                    message="Bot session closed",
                    category='system'
                )
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error closing bot session: {str(e)}",
                category='system',
                exception=e
            )
    
    async def _log_final_statistics(self):
        """Записать финальную статистику"""
        try:
            if self.monitoring_service:
                service_stats = self.monitoring_service.get_service_stats()
                error_stats = error_handler.get_stats()
                shutdown_status = shutdown_manager.get_shutdown_status()
                
                structured_logger.log_structured(
                    level='INFO',
                    message="Final bot statistics",
                    category='system',
                    extra_data={
                        'monitoring': service_stats,
                        'error_handler': error_stats,
                        'shutdown': shutdown_status
                    }
                )
            
        except Exception as e:
            structured_logger.log_structured(
                level='ERROR',
                message=f"Error logging final statistics: {str(e)}",
                category='system',
                exception=e
            )
    
    async def _before_shutdown(self):
        """Действия перед завершением"""
        structured_logger.log_structured(
            level='INFO',
            message="Performing pre-shutdown actions...",
            category='system'
        )
        
        # Отменяем все выполняющиеся задачи
        await shutdown_manager.cancel_all_running_tasks()
    
    async def _after_shutdown(self):
        """Действия после завершения"""
        structured_logger.log_structured(
            level='INFO',
            message="Post-shutdown actions completed",
            category='system'
        )
        
        self.is_running = False


# ============= Глобальный экземпляр и точка входа =============

bot_instance: Optional[ModernTurboPingBot] = None


def get_bot_instance() -> Optional[ModernTurboPingBot]:
    """Получить экземпляр бота для внешнего доступа"""
    return bot_instance


async def main():
    """Главная точка входа"""
    global bot_instance
    
    try:
        bot_instance = ModernTurboPingBot()
        await bot_instance.start()
        
    except KeyboardInterrupt:
        structured_logger.log_structured(
            level='INFO',
            message="Bot stopped by user",
            category='system'
        )
    except Exception as e:
        structured_logger.log_structured(
            level='CRITICAL',
            message=f"Critical error in main: {str(e)}",
            category='system',
            severity='critical',
            exception=e
        )
        sys.exit(1)
    finally:
        # Гарантируем завершение работы
        if shutdown_manager.is_shutdown_requested():
            await shutdown_manager.wait_for_shutdown(timeout=30.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        sys.exit(1)