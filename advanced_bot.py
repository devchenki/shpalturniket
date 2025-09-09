"""
TurboShpalych Pro Bot - Продвинутый Telegram бот для мониторинга турникетов
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Современная переработанная версия с улучшенной архитектурой и пользовательским опытом.
"""

import asyncio
import logging
import json
import importlib
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    Message
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import monitoring modules
try:
    import Ping
    importlib.reload(Ping)
    from Ping import Ping_IP
    logger.info("✅ Ping модуль загружен успешно")
except Exception as ping_error:
    logger.error(f"❌ Ошибка загрузки Ping модуля: {ping_error}")
    print(f"❌ Ошибка загрузки Ping модуля: {ping_error}")
    raise

try:
    from Read_config import TOKEN, time_connect, chat_id, read_config
    logger.info("✅ Конфигурация загружена успешно")
except Exception as config_error:
    logger.error(f"❌ Ошибка загрузки конфигурации: {config_error}")
    print(f"❌ Ошибка загрузки конфигурации: {config_error}")
    raise

# ============= Модели данных =============

@dataclass
class DeviceInfo:
    """Модель информации об устройстве"""
    id: str
    ip: str
    location: str
    category: str
    status: Optional[str] = None
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None

@dataclass
class CategoryInfo:
    """Модель информации о категории"""
    id: str
    name: str
    icon: str
    devices: List[str] = field(default_factory=list)
    
class DeviceStatus(Enum):
    """Перечисление статусов устройств"""
    ONLINE = "онлайн"
    OFFLINE = "офлайн"
    CHECKING = "проверка"
    UNKNOWN = "неизвестно"

class UserStates(StatesGroup):
    """Состояния взаимодействия пользователя"""
    main_menu = State()
    viewing_category = State()
    viewing_device = State()
    waiting_input = State()

# ============= Компоненты интерфейса =============

class UIComponents:
    """Строитель современных компонентов интерфейса"""
    
    @staticmethod
    def create_button(text: str, callback_data: str, emoji: str = "") -> InlineKeyboardButton:
        """Создать стилизованную кнопку"""
        button_text = f"{emoji} {text}" if emoji else text
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)
    
    @staticmethod
    def create_keyboard(buttons: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
        """Создать клавиатуру с правильной компоновкой"""
        builder = InlineKeyboardBuilder()
        for row in buttons:
            builder.row(*row)
        return builder.as_markup()
    
    @staticmethod
    def format_device_status(device: DeviceInfo) -> str:
        """Форматировать статус устройства с современными иконками"""
        status_icons = {
            DeviceStatus.ONLINE: "🟢",
            DeviceStatus.OFFLINE: "🔴",
            DeviceStatus.CHECKING: "🟡",
            DeviceStatus.UNKNOWN: "⚪"
        }
        
        status_icon = status_icons.get(
            DeviceStatus(device.status) if device.status else DeviceStatus.UNKNOWN,
            "⚪"
        )
        
        return f"{status_icon} <b>{device.id}</b> • {device.ip}"
    
    @staticmethod
    def create_progress_bar(current: int, total: int, width: int = 10) -> str:
        """Создать текстовую полосу прогресса"""
        if total == 0:
            return "⬜" * width
        
        percentage = current / total
        filled = int(percentage * width)
        empty = width - filled
        
        return "🟩" * filled + "⬜" * empty

    @staticmethod
    def format_two_columns(items: List[str], col_width: int = 28) -> str:
        """Форматировать список строк в две колонки в <pre>"""
        if not items:
            return "<pre>—</pre>"
        
        # Разделяем на две колонки
        left_col = []
        right_col = []
        for i, item in enumerate(items):
            if i % 2 == 0:
                left_col.append(item)
            else:
                right_col.append(item)
        
        # Выравниваем длину колонок
        max_len = max(len(left_col), len(right_col))
        left_col += [""] * (max_len - len(left_col))
        right_col += [""] * (max_len - len(right_col))
        
        # Формируем строки
        lines = []
        for left_item, right_item in zip(left_col, right_col):
            left_padded = (left_item or "").ljust(col_width)
            right_text = right_item or ""
            lines.append(f"{left_padded}  {right_text}")
        
        return "<pre>" + "\n".join(lines) + "</pre>"

# ============= Слой сервисов =============

class MonitoringService:
    """Сервис для операций мониторинга устройств"""
    
    def __init__(self, ping_instance: Ping_IP):
        self.ping = ping_instance
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 30  # seconds
        
    async def check_device(self, device: DeviceInfo) -> DeviceInfo:
        """Проверить статус одного устройства с прямым ping_ip"""
        try:
            is_online = await asyncio.to_thread(self.ping.ping_ip, device.ip)
            device.last_check = datetime.now()
            if is_online:
                device.status = DeviceStatus.ONLINE.value
                # Замеряем время отклика повторыным ping
                try:
                    import time as _t
                    t0 = _t.perf_counter()
                    await asyncio.to_thread(self.ping.ping_ip, device.ip)
                    device.response_time = (_t.perf_counter() - t0) * 1000.0
                except Exception:
                    device.response_time = None
            else:
                device.status = DeviceStatus.OFFLINE.value
                device.response_time = None
        except Exception as e:
            logger.error(f"Ошибка проверки устройства {device.id}: {e}")
            device.status = DeviceStatus.UNKNOWN.value
            device.last_check = datetime.now()
            device.response_time = None
        return device
    
    async def check_multiple_devices(self, devices: List[DeviceInfo]) -> List[DeviceInfo]:
        """Проверить несколько устройств одновременно"""
        tasks = [self.check_device(device) for device in devices]
        return await asyncio.gather(*tasks)
    
    def get_statistics(self, devices: List[DeviceInfo]) -> Dict[str, Any]:
        """Рассчитать статистику мониторинга"""
        total = len(devices)
        online = sum(1 for d in devices if d.status == DeviceStatus.ONLINE.value)
        offline = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE.value)
        
        return {
            'total': total,
            'online': online,
            'offline': offline,
            'percentage': (online / total * 100) if total > 0 else 0,
            'last_update': datetime.now()
        }

# ============= Основной класс бота =============

class ModernTurboPingBot:
    """Современный переработанный TurboShpalych Pro бот"""
    
    def __init__(self):
        self.bot = Bot(token=TOKEN)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.log_callback = None  # Callback для логирования в GUI
        
        # Инициализация компонентов
        self.ping = Ping_IP()
        self.monitoring_service = MonitoringService(self.ping)
        self.ui = UIComponents()
        
        self.devices: Dict[str, DeviceInfo] = {}
        self.categories: Dict[str, CategoryInfo] = {}
        
        self._initialize()
        self._register_handlers()
        
        # Хелпер: формирование стартовой сводки
    def _build_startup_summary_messages(self, devices: List[DeviceInfo]) -> List[str]:
        try:
            stats = self.monitoring_service.get_statistics(devices)
            online = [d for d in devices if d.status == DeviceStatus.ONLINE.value]
            offline = [d for d in devices if d.status == DeviceStatus.OFFLINE.value]
            header = (
                f"<b>🚀 Стартовая сводка</b>\n\n"
                f"Всего: {stats['total']} | 🟢 {stats['online']} | 🔴 {stats['offline']}\n"
                f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            parts: List[str] = [header]
            # Формируем таблицы
            def build_table(title: str, items: List[DeviceInfo]) -> str:
                rows = [f"{d.id} — {d.ip}" for d in sorted(items, key=lambda x: x.id)]
                return f"<b>{title}</b>\n" + self.ui.format_two_columns(rows, col_width=30)
            parts.append(build_table("🟢 Онлайн", online))
            parts.append(build_table("🔴 Офлайн", offline))
            # Разбиваем по лимиту Telegram
            messages: List[str] = []
            current = ""
            for part in parts:
                if len(current) + len(part) + 2 > 3800:  # запас для HTML
                    messages.append(current)
                    current = part
                else:
                    current = (current + "\n\n" + part) if current else part
            if current:
                messages.append(current)
            return [m for m in messages if m.strip()]
        except Exception as e:
            logger.error(f"Ошибка формирования сводки: {e}")
            return []
    
    def set_log_callback(self, callback):
        """Устанавливает callback для логирования в GUI"""
        self.log_callback = callback
    
    def get_alert_chats(self) -> List[int]:
        """Нормализовать chat_id из конфигурации в список int"""
        try:
            from Read_config import chat_id as cfg_chat
        except Exception:
            cfg_chat = chat_id
        result: List[int] = []
        try:
            if isinstance(cfg_chat, (list, tuple)):
                for x in cfg_chat:
                    try:
                        result.append(int(x))
                    except Exception:
                        pass
            elif isinstance(cfg_chat, str):
                parts = [p.strip() for p in cfg_chat.replace(';', ',').split(',') if p.strip()]
                for p in parts:
                    try:
                        result.append(int(p))
                    except Exception:
                        pass
            else:
                result = [int(cfg_chat)]
        except Exception:
            pass
        return result
    
    def log_to_gui(self, message):
        """Отправляет сообщение в GUI через callback"""
        if self.log_callback:
            self.log_callback(message)
        # Также логируем в консоль
        logger.info(message)
    
    async def send_alert_to_all_chats(self, message):
        """Отправляет уведомление во все настроенные чаты"""
        try:
            # Список чатов для уведомлений
            alert_chats = self.get_alert_chats()
            
            for chat in alert_chats:
                try:
                    await self.bot.send_message(
                        chat_id=chat,
                        text=message,
                        parse_mode="HTML"
                    )
                    self.log_to_gui(f"📤 Уведомление отправлено в чат {chat}")
                except Exception as e:
                    self.log_to_gui(f"❌ Ошибка отправки в чат {chat}: {e}")
                    
        except Exception as e:
            self.log_to_gui(f"❌ Ошибка отправки уведомлений: {e}")
        
    def _initialize(self):
        """Инициализировать конфигурацию и данные бота"""
        self._load_configuration()
        self._categorize_devices()
        logger.info(f"✅ Бот инициализирован с {len(self.devices)} устройствами в {len(self.categories)} категориях")
        
    def _load_configuration(self):
        """Загрузить конфигурацию устройств"""
        try:
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
            
            logger.info(f"📋 Загружено {len(self.devices)} устройств из конфигурации")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
            self.devices = {}
    
    def _categorize_devices(self):
        """Организовать устройства по категориям"""
        category_config = {
            'C': ('Центральный C', '🏢'),
            'D': ('Проход D', '🚶'),
            'E': ('Эскалатор E', '🚇'),
            'F': ('Переход F', '🔄'),
            'G': ('Вход G', '🚪'),
            'H': ('Зал H', '🏛️')
        }
        
        for cat_id, (name, icon) in category_config.items():
            self.categories[cat_id] = CategoryInfo(
                id=cat_id,
                name=name,
                icon=icon
            )
        
        for device in self.devices.values():
            if device.category in self.categories:
                self.categories[device.category].devices.append(device.id)
        
        # Удаляем пустые категории
        self.categories = {
            k: v for k, v in self.categories.items() 
            if v.devices
        }
    
    def _register_handlers(self):
        """Зарегистрировать все обработчики сообщений и обратных вызовов"""
        # Обработчики команд
        self.dp.message.register(self.cmd_start, CommandStart())
        self.dp.message.register(self.cmd_help, Command('help'))
        self.dp.message.register(self.cmd_stats, Command('stats'))
        
        # Обработчики обратных вызовов с паттернами
        self.dp.callback_query.register(self.handle_main_menu, F.data == "main_menu")
        self.dp.callback_query.register(self.handle_system_status, F.data == "system_status")
        self.dp.callback_query.register(self.handle_statistics, F.data == "statistics")
        self.dp.callback_query.register(self.handle_all_devices, F.data == "all_devices")
        self.dp.callback_query.register(self.handle_online_devices, F.data == "online_devices")
        self.dp.callback_query.register(self.handle_offline_devices, F.data == "offline_devices")
        self.dp.callback_query.register(self.handle_categories, F.data == "categories")
        self.dp.callback_query.register(self.handle_device_ping_menu, F.data == "device_ping_menu")
        self.dp.callback_query.register(self.handle_help, F.data == "help")
        
        # Динамические паттерны обратных вызовов
        self.dp.callback_query.register(
            self.handle_category_view, 
            F.data.startswith("cat_")
        )
        self.dp.callback_query.register(
            self.handle_device_check, 
            F.data.startswith("device_")
        )
        self.dp.callback_query.register(
            self.handle_device_ping, 
            F.data.startswith("ping_")
        )
        self.dp.callback_query.register(
            self.handle_refresh, 
            F.data.startswith("refresh_")
        )
    
    # ============= Обработчики команд =============
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Обработать команду /start"""
        await state.set_state(UserStates.main_menu)
        
        user_id = message.from_user.id
        user_name = message.from_user.full_name or "Неизвестный"
        username = message.from_user.username or "без_username"
        
        # Детальное логирование в GUI
        self.log_to_gui(f"👤 Пользователь {user_name} (@{username}, ID: {user_id}) отправил команду /start")
        
        user_info = f"Пользователь {user_id} (@{username})"
        logger.info(f"🚀 Команда start от {user_info}")
        
        keyboard = self._create_main_menu_keyboard()
        
        stats = self.monitoring_service.get_statistics(list(self.devices.values()))
        
        welcome_text = f"""
<b>🤖 TurboShpalych Pro - Система мониторинга турникетов от Шпалыча</b>

Добро пожаловать, {message.from_user.first_name}! 👋

<b>📊 Обзор системы:</b>
├ 📡 Устройств: {stats['total']}
├ 🟢 Онлайн: {stats['online']}
├ 🔴 Офлайн: {stats['offline']}
├ 📈 Время работы: {stats['percentage']:.1f}%
└ 🏗️ Категорий: {len(self.categories)}

<b>⚙️ Конфигурация:</b>
├ ⏱️ Интервал проверки: {time_connect}с
├ 👤 Ваш ID: <code>{message.from_user.id}</code>
└ 🕐 Время: {datetime.now().strftime('%H:%M:%S')}

Выберите действие ниже:
"""
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        self.log_to_gui(f"📨 Отправлено главное меню пользователю {user_name} (ID: {user_id})")
    
    async def cmd_help(self, message: Message):
        """Обработать команду /help"""
        await self.send_help_message(message)
    
    async def cmd_stats(self, message: Message):
        """Обработать команду /stats"""
        await self.send_statistics_message(message)
    
    # ============= Обработчики обратных вызовов =============
    
    async def handle_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Обработать обратный вызов главного меню"""
        user_id = callback.from_user.id
        user_name = callback.from_user.full_name or "Неизвестный"
        username = callback.from_user.username or "без_username"
        
        self.log_to_gui(f"📱 {user_name} (@{username}, ID: {user_id}) нажал 'Главное меню'")
        
        await state.set_state(UserStates.main_menu)
        await self.show_main_menu(callback.message)
        await callback.answer()
    
    async def handle_system_status(self, callback: CallbackQuery):
        """Обработать запрос статуса системы"""
        user_id = callback.from_user.id
        user_name = callback.from_user.full_name or "Неизвестный"
        username = callback.from_user.username or "без_username"
        
        self.log_to_gui(f"🔍 {user_name} (@{username}, ID: {user_id}) запросил статус системы")
        
        await callback.answer("🔄 Проверка статуса системы...")
        await self.show_system_status(callback.message)
        
        self.log_to_gui(f"📊 Отправлен статус системы для {user_name}")
    
    async def handle_statistics(self, callback: CallbackQuery):
        """Обработать запрос статистики"""
        user_id = callback.from_user.id
        user_name = callback.from_user.full_name or "Неизвестный"
        username = callback.from_user.username or "без_username"
        
        self.log_to_gui(f"📈 {user_name} (@{username}, ID: {user_id}) запросил статистику")
        
        await callback.answer("📊 Загрузка статистики...")
        await self.send_statistics_message(callback.message)
        
        self.log_to_gui(f"📊 Отправлена статистика для {user_name}")
    
    async def handle_all_devices(self, callback: CallbackQuery):
        """Обработать просмотр всех устройств"""
        await callback.answer("📋 Загрузка всех устройств...")
        await self.show_all_devices(callback.message)
    
    async def handle_online_devices(self, callback: CallbackQuery):
        """Обработать просмотр онлайн устройств"""
        await callback.answer("🟢 Загрузка онлайн устройств...")
        await self.show_filtered_devices(callback.message, DeviceStatus.ONLINE)
    
    async def handle_offline_devices(self, callback: CallbackQuery):
        """Обработать просмотр офлайн устройств"""
        await callback.answer("🔴 Загрузка офлайн устройств...")
        await self.show_filtered_devices(callback.message, DeviceStatus.OFFLINE)
    
    async def handle_categories(self, callback: CallbackQuery):
        """Обработать просмотр категорий"""
        await callback.answer("🏗️ Загрузка категорий...")
        await self.show_categories(callback.message)
    
    async def handle_help(self, callback: CallbackQuery):
        """Обработать запрос помощи"""
        await callback.answer()
        await self.send_help_message(callback.message)
    
    async def handle_device_ping_menu(self, callback: CallbackQuery):
        """Показать меню пинга устройств"""
        await callback.answer("Загрузка меню пинга...")
        
        # Создаем кнопки устройств в 3 столбца
        device_buttons = []
        devices = list(self.devices.values())
        
        # Группируем устройства по 3 в ряд
        for i in range(0, len(devices), 3):
            row = []
            for j in range(3):
                if i + j < len(devices):
                    device = devices[i + j]
                    # Сокращаем название для кнопки
                    button_text = device.id[:8] + "..." if len(device.id) > 8 else device.id
                    row.append(self.ui.create_button(
                        button_text, 
                        f"ping_{device.id}", 
                        "🎯"
                    ))
            device_buttons.append(row)
        
        # Добавляем кнопку "Назад"
        device_buttons.append([
            self.ui.create_button("🔙 Назад", "main_menu", "🔙")
        ])
        
        keyboard = self.ui.create_keyboard(device_buttons)
        
        text = f"""
<b>🎯 Меню пинга устройств</b>

Выберите устройство для проверки связи:
📱 Всего устройств: {len(devices)}

💡 <i>Нажмите на кнопку устройства для выполнения пинга</i>
"""
        
        try:
            await callback.message.edit_text(
                text, 
                parse_mode="HTML", 
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.answer(
                text, 
                parse_mode="HTML", 
                reply_markup=keyboard
            )
    
    async def handle_device_ping(self, callback: CallbackQuery):
        """Обработать пинг конкретного устройства"""
        device_id = callback.data.replace("ping_", "")
        await callback.answer(f"🎯 Пингую {device_id}...")
        
        if device_id not in self.devices:
            await callback.message.answer("❌ Устройство не найдено!")
            return
        
        device = self.devices[device_id]
        
        # Выполняем проверку устройства
        updated_device = await self.monitoring_service.check_device(device)
        
        # Определяем статус и эмодзи
        if updated_device.status == DeviceStatus.ONLINE.value:
            status_emoji = "🟢"
            status_text = "ОНЛАЙН"
            color = "🟢"
        elif updated_device.status == DeviceStatus.OFFLINE.value:
            status_emoji = "🔴"
            status_text = "ОФЛАЙН"
            color = "🔴"
        else:
            status_emoji = "⚪"
            status_text = "НЕИЗВЕСТНО"
            color = "⚪"
        
        # Логируем действие пользователя
        user_info = f"{callback.from_user.full_name} (@{callback.from_user.username or 'N/A'}, ID: {callback.from_user.id})"
        self.log_to_gui(f"🎯 {user_info} выполнил пинг устройства {device_id} - результат: {status_text}")
        
        # Формируем ответ
        response_text = f"""
{status_emoji} <b>Результат пинга устройства</b>

📍 <b>Устройство:</b> {device.id}
🌐 <b>IP:</b> <code>{device.ip}</code>
📍 <b>Местоположение:</b> {device.location}
{color} <b>Статус:</b> {status_text}
⏰ <b>Время проверки:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}

{'✅ Устройство отвечает!' if updated_device.status == DeviceStatus.ONLINE.value else '❌ Устройство не отвечает!'}
"""
        
        # Создаем кнопки для дальнейших действий
        action_buttons = [
            [
                self.ui.create_button("🔄 Повторить", f"ping_{device_id}", "🔄"),
                self.ui.create_button("🔙 К списку", "device_ping_menu", "🔙")
            ],
            [
                self.ui.create_button("🏠 Главное меню", "main_menu", "🏠")
            ]
        ]
        
        keyboard = self.ui.create_keyboard(action_buttons)
        
        try:
            await callback.message.edit_text(
                response_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception:
            await callback.message.answer(
                response_text,
                parse_mode="HTML", 
                reply_markup=keyboard
            )
    
    async def handle_category_view(self, callback: CallbackQuery, state: FSMContext):
        """Обработать просмотр устройств категории"""
        category_id = callback.data.replace("cat_", "")
        await state.set_state(UserStates.viewing_category)
        await state.update_data(category_id=category_id)
        await callback.answer(f"Загрузка категории {category_id}...")
        await self.show_category_devices(callback.message, category_id)
    
    async def handle_device_check(self, callback: CallbackQuery, state: FSMContext):
        """Обработать проверку одного устройства"""
        user_id = callback.from_user.id
        user_name = callback.from_user.full_name or "Неизвестный"
        username = callback.from_user.username or "без_username"
        
        device_id = callback.data.replace("device_", "")
        
        self.log_to_gui(f"🔍 {user_name} (@{username}, ID: {user_id}) запросил проверку устройства: {device_id}")
        
        await state.set_state(UserStates.viewing_device)
        await state.update_data(device_id=device_id)
        await callback.answer(f"🔍 Проверка {device_id}...")
        await self.check_single_device(callback.message, device_id)
        
        self.log_to_gui(f"📤 Выполнен пинг устройства {device_id} для {user_name}")
    
    async def handle_refresh(self, callback: CallbackQuery):
        """Обработать действие обновления"""
        action = callback.data.replace("refresh_", "")
        await callback.answer("🔄 Обновление...")
        
        if action == "status":
            await self.show_system_status(callback.message)
        elif action == "all":
            await self.show_all_devices(callback.message)
        elif action in ("онлайн", "офлайн"):
            await self.show_filtered_devices(
                callback.message,
                DeviceStatus.ONLINE if action == "онлайн" else DeviceStatus.OFFLINE
            )
        elif action.startswith("device_"):
            device_id = action.replace("device_", "")
            await self.check_single_device(callback.message, device_id)
    
    # ============= Методы интерфейса =============
    
    def _create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Создать клавиатуру главного меню"""
        return self.ui.create_keyboard([
            [
                self.ui.create_button("Статус системы", "system_status", "📊"),
                self.ui.create_button("Статистика", "statistics", "📈")
            ],
            [
                self.ui.create_button("Онлайн", "online_devices", "🟢"),
                self.ui.create_button("Офлайн", "offline_devices", "🔴")
            ],
            [
                self.ui.create_button("Все устройства", "all_devices", "📋"),
                self.ui.create_button("Категории", "categories", "🏗️")
            ],
            [
                self.ui.create_button("🎯 Пинг устройств", "device_ping_menu", "🎯")
            ],
            [
                self.ui.create_button("Помощь", "help", "ℹ️")
            ]
        ])
    
    async def show_main_menu(self, message: Message):
        """Показать главное меню"""
        keyboard = self._create_main_menu_keyboard()
        stats = self.monitoring_service.get_statistics(list(self.devices.values()))
        
        text = f"""
<b>🤖 TurboShpalych Pro - Главное меню</b>

<b>📊 Быстрая статистика:</b>
{self.ui.create_progress_bar(stats['online'], stats['total'])} {stats['percentage']:.1f}%

├ 📡 Всего: {stats['total']}
├ 🟢 Онлайн: {stats['online']}
├ 🔴 Офлайн: {stats['offline']}
└ 🏗️ Категорий: {len(self.categories)}

Выберите опцию:
"""
        
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        except TelegramBadRequest:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def show_system_status(self, message: Message):
        """Показать детальный статус системы"""
        # Показать сообщение загрузки
        loading_msg = await message.edit_text("🔄 <b>Анализ статуса системы...</b>", parse_mode="HTML")
        
        # Проверить все устройства
        devices_list = list(self.devices.values())
        checked_devices = await self.monitoring_service.check_multiple_devices(devices_list)
        
        # Обновить статус устройств
        for device in checked_devices:
            self.devices[device.id] = device
        
        stats = self.monitoring_service.get_statistics(checked_devices)
        
        # Две колонки: список всех устройств
        rows = [f"{('🟢' if d.status == DeviceStatus.ONLINE.value else '🔴' if d.status == DeviceStatus.OFFLINE.value else '⚪')} {d.id} — {d.ip}" for d in sorted(checked_devices, key=lambda x: x.id)]
        table = self.ui.format_two_columns(rows, col_width=30)

        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Обновить", "refresh_status", "🔄")],
            [
                self.ui.create_button("Главное меню", "main_menu", "🏠"),
                self.ui.create_button("Детали", "all_devices", "📋")
            ]
        ])
        
        status_text = f"""
<b>📊 Отчет о статусе системы</b>

<b>🎯 Общее состояние:</b>
{self.ui.create_progress_bar(stats['online'], stats['total'])} {stats['percentage']:.1f}%

<b>📈 Статистика:</b>
├ 📡 Всего устройств: {stats['total']}
├ 🟢 Онлайн: {stats['online']} ({stats['online']/stats['total']*100:.1f}%)
├ 🔴 Офлайн: {stats['offline']} ({stats['offline']/stats['total']*100:.1f}%)
└ ⏱️ Интервал проверки: {time_connect}с

<b>📋 Устройства:</b>
{table}

<b>⏰ Последнее обновление:</b> {stats['last_update'].strftime('%H:%M:%S')}
"""
        
        await loading_msg.edit_text(status_text, parse_mode="HTML", reply_markup=keyboard)
    
    async def show_all_devices(self, message: Message):
        """Показать все устройства с их статусом"""
        loading_msg = await message.edit_text("🔄 <b>Проверка всех устройств...</b>", parse_mode="HTML")
        
        # Проверить все устройства
        devices_list = list(self.devices.values())
        checked_devices = await self.monitoring_service.check_multiple_devices(devices_list)
        
        # Обновить локальные статусы устройств
        for device in checked_devices:
            self.devices[device.id] = device
        
        # Полный список в две колонки
        rows = [f"{('🟢' if d.status == DeviceStatus.ONLINE.value else '🔴' if d.status == DeviceStatus.OFFLINE.value else '⚪')} {d.id} — {d.ip}" for d in sorted(checked_devices, key=lambda x: x.id)]
        table = self.ui.format_two_columns(rows, col_width=30)

        stats = self.monitoring_service.get_statistics(checked_devices)
        output_lines = ["<b>📋 Статус всех устройств</b>", table, f"<b>📊 Итого:</b> 🟢 {stats['online']} | 🔴 {stats['offline']}"]

        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Обновить", "refresh_all", "🔄")],
            [
                self.ui.create_button("Только онлайн", "online_devices", "🟢"),
                self.ui.create_button("Только офлайн", "offline_devices", "🔴")
            ],
            [self.ui.create_button("Главное меню", "main_menu", "🏠")]
        ])
        
        await loading_msg.edit_text(
            "\n".join(output_lines),
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def show_filtered_devices(self, message: Message, status_filter: DeviceStatus):
        """Показать устройства, отфильтрованные по статусу"""
        loading_msg = await message.edit_text(
            f"🔄 <b>Проверка {status_filter.value} устройств...</b>",
            parse_mode="HTML"
        )
        
        # Проверить все устройства
        devices_list = list(self.devices.values())
        checked_devices = await self.monitoring_service.check_multiple_devices(devices_list)
        
        # Обновить локальные статусы устройств
        for device in checked_devices:
            self.devices[device.id] = device
        
        # Отфильтровать устройства
        filtered = [d for d in checked_devices if d.status == status_filter.value]
        status_emoji = "🟢" if status_filter == DeviceStatus.ONLINE else "🔴"
        header = f"<b>{status_emoji} {status_filter.value.title()} устройств ({len(filtered)})</b>"
        rows = [f"{d.id} — {d.ip}" for d in sorted(filtered, key=lambda x: x.id)]
        table = self.ui.format_two_columns(rows, col_width=30)
        text = header + "\n" + table
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Обновить", f"refresh_{'онлайн' if status_filter==DeviceStatus.ONLINE else 'офлайн'}", "🔄")],
            [self.ui.create_button("Все устройства", "all_devices", "📋")],
            [self.ui.create_button("Главное меню", "main_menu", "🏠")]
        ])
        
        await loading_msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def show_categories(self, message: Message):
        """Показать категории устройств"""
        # Создать кнопки категорий
        button_rows = []
        for cat_id, cat_info in self.categories.items():
            button = self.ui.create_button(
                f"{cat_info.name} ({len(cat_info.devices)})",
                f"cat_{cat_id}",
                cat_info.icon
            )
            button_rows.append([button])
        
        button_rows.append([self.ui.create_button("Главное меню", "main_menu", "🏠")])
        
        keyboard = self.ui.create_keyboard(button_rows)
        
        text = f"""
<b>🏗️ Категории устройств</b>

Выберите категорию для просмотра устройств:

<b>📊 Обзор категорий:</b>
"""
        for cat_id, cat_info in self.categories.items():
            text += f"\n{cat_info.icon} <b>{cat_info.name}:</b> {len(cat_info.devices)} устройств"
        
        text += f"\n\n<b>Всего:</b> {len(self.devices)} устройств в {len(self.categories)} категориях"
        
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def show_category_devices(self, message: Message, category_id: str):
        """Показать устройства в конкретной категории"""
        if category_id not in self.categories:
            await message.edit_text("❌ Категория не найдена")
            return
        
        cat_info = self.categories[category_id]
        devices = [self.devices[d_id] for d_id in cat_info.devices if d_id in self.devices]
        
        # Проверить устройства
        loading_msg = await message.edit_text(
            f"🔄 <b>Проверка устройств {cat_info.name}...</b>",
            parse_mode="HTML"
        )
        
        checked_devices = await self.monitoring_service.check_multiple_devices(devices)
        
        # Форматировать вывод
        lines = [f"{cat_info.icon} <b>{cat_info.name}</b>\n"]
        
        for device in checked_devices:
            lines.append(self.ui.format_device_status(device))
            lines.append(f"  📍 {device.location}\n")
        
        stats = self.monitoring_service.get_statistics(checked_devices)
        lines.append(f"<b>📊 Итого:</b> 🟢 {stats['online']} | 🔴 {stats['offline']}")
        
        # Создать кнопки проверки устройств
        button_rows = []
        for device in checked_devices[:6]:  # Ограничить кнопки
            button = self.ui.create_button(
                device.id,
                f"device_{device.id}",
                "🔍"
            )
            button_rows.append([button])
        
        button_rows.append([
            self.ui.create_button("Категории", "categories", "🏗️"),
            self.ui.create_button("Главное меню", "main_menu", "🏠")
        ])
        
        keyboard = self.ui.create_keyboard(button_rows)
        
        await loading_msg.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def check_single_device(self, message: Message, device_id: str):
        """Проверить детальный статус одного устройства"""
        if device_id not in self.devices:
            await message.edit_text("❌ Устройство не найдено")
            return
        
        device = self.devices[device_id]
        
        # Проверить устройство
        loading_msg = await message.edit_text(
            f"🔍 <b>Проверка {device_id}...</b>",
            parse_mode="HTML"
        )
        
        checked_device = await self.monitoring_service.check_device(device)
        self.devices[device_id] = checked_device
        
        # Форматировать детальную информацию
        status_emoji = "🟢" if checked_device.status == DeviceStatus.ONLINE.value else "🔴"
        cat_info = self.categories.get(checked_device.category, None)
        
        text = f"""
<b>🔍 Детали устройства</b>

{status_emoji} <b>{checked_device.id}</b>

<b>📋 Информация:</b>
├ 🌐 IP: <code>{checked_device.ip}</code>
├ 📍 Расположение: {checked_device.location}
├ 🏗️ Категория: {cat_info.icon + ' ' + cat_info.name if cat_info else 'Неизвестно'}
└ 📊 Статус: {checked_device.status}

<b>⏰ Последняя проверка:</b> {checked_device.last_check.strftime('%H:%M:%S') if checked_device.last_check else 'Никогда'}
"""
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Проверить снова", f"refresh_device_{device_id}", "🔄")],
            [
                self.ui.create_button("Категория", f"cat_{checked_device.category}", "🏗️"),
                self.ui.create_button("Все устройства", "all_devices", "📋")
            ],
            [self.ui.create_button("Главное меню", "main_menu", "🏠")]
        ])
        
        await loading_msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    
    async def send_help_message(self, message: Message):
        """Отправить сообщение помощи"""
        help_text = f"""
<b>ℹ️ Справка TurboShpalych Pro </b>

<b>🎯 Возможности:</b>
• Мониторинг устройств в реальном времени
• Организация по категориям
• Детальная статистика
• Быстрые проверки статуса

<b>📱 Команды:</b>
• /start - Главное меню
• /help - Это сообщение помощи
• /stats - Быстрая статистика

<b>🏗️ Категории:</b>
• Каждое устройство организовано по типу
• Быстрый доступ к связанным устройствам
• Пакетные проверки статуса

<b>💡 Советы:</b>
• Используйте 🔄 для обновления данных
• Нажимайте на имена устройств для деталей
• Проверяйте категории для группового просмотра

<b>🆔 Ваш ID:</b> <code>{message.from_user.id if hasattr(message, 'from_user') else message.chat.id}</code>

<b>⚙️ Система:</b>  Шпалыч эдишн
"""
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Главное меню", "main_menu", "🏠")]
        ])
        
        try:
            await message.edit_text(help_text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)
    
    async def send_statistics_message(self, message: Message):
        """Отправить детальную статистику"""
        # Проверить все устройства для свежей статистики
        devices_list = list(self.devices.values())
        checked_devices = await self.monitoring_service.check_multiple_devices(devices_list)
        
        stats = self.monitoring_service.get_statistics(checked_devices)
        online_list = [d for d in checked_devices if d.status == DeviceStatus.ONLINE.value]
        offline_list = [d for d in checked_devices if d.status == DeviceStatus.OFFLINE.value]

        online_rows = [f"{d.id} — {d.ip}" for d in sorted(online_list, key=lambda x: x.id)]
        offline_rows = [f"{d.id} — {d.ip}" for d in sorted(offline_list, key=lambda x: x.id)]
        online_table = self.ui.format_two_columns(online_rows, col_width=30)
        offline_table = self.ui.format_two_columns(offline_rows, col_width=30)

        text = f"""
<b>📈 Детальная статистика</b>

<b>🎯 Общая производительность:</b>
{self.ui.create_progress_bar(stats['online'], stats['total'])} {stats['percentage']:.1f}%

<b>📊 Общая статистика:</b>
├ 📡 Всего устройств: {stats['total']}
├ 🟢 Онлайн: {stats['online']} ({stats['percentage']:.1f}%)
├ 🔴 Офлайн: {stats['offline']} ({100 - stats['percentage']:.1f}%)
└ ⏱️ Интервал проверки: {time_connect}с

<b>🟢 Онлайн:</b>
{online_table}

<b>🔴 Офлайн:</b>
{offline_table}

<b>⏰ Сгенерировано:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Обновить", "statistics", "🔄")],
            [self.ui.create_button("Главное меню", "main_menu", "🏠")]
        ])
        
        try:
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    
    # ============= Жизненный цикл бота =============
    
    async def start(self):
        """Запустить бота"""
        self.log_to_gui("🚀 Запуск современного TurboShpalych Pro бота...")
        
        try:
            # На всякий случай отключаем вебхук, чтобы Long Polling получал апдейты
            try:
                await self.bot.delete_webhook(drop_pending_updates=True)
                self.log_to_gui("🌐 Вебхук отключен (переходим на long polling)")
            except Exception as e:
                self.log_to_gui(f"⚠️ Не удалось отключить вебхук: {e}")

            # Установить команды бота
            await self.bot.set_my_commands([
                types.BotCommand(command="start", description="Открыть главное меню"),
                types.BotCommand(command="help", description="Показать справку"),
                types.BotCommand(command="stats", description="Показать статистику")
            ])
            
            self.log_to_gui("📋 Команды Telegram бота установлены")
            self.log_to_gui("✅ Telegram бот успешно запущен и готов к работе!")
            self.log_to_gui("📱 Отправьте /start в Telegram для начала работы")

            # Стартовая проверка всех устройств и отправка сводки
            try:
                devices_list = list(self.devices.values())
                checked = await self.monitoring_service.check_multiple_devices(devices_list)
                # Обновляем локальные статусы
                for d in checked:
                    self.devices[d.id] = d
                summary_msgs = self._build_startup_summary_messages(checked)
                for msg in summary_msgs:
                    await self.send_alert_to_all_chats(msg)
            except Exception as e:
                self.log_to_gui(f"⚠️ Не удалось отправить стартовую сводку: {e}")
            
            # Запустить опрос
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
            
        except Exception as e:
            error_msg = f"❌ Ошибка бота: {e}"
            self.log_to_gui(error_msg)
            logger.error(error_msg)
        finally:
            await self.bot.session.close()
            self.log_to_gui("🔒 Бот остановлен")

# ============= Глобальный экземпляр =============

bot_instance: Optional[ModernTurboPingBot] = None

def get_bot_instance() -> Optional[ModernTurboPingBot]:
    """Получить экземпляр бота для внешнего доступа"""
    return bot_instance

async def main():
    """Главная точка входа"""
    global bot_instance
    bot_instance = ModernTurboPingBot()
    await bot_instance.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)