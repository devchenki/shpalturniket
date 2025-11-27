#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Components for TurboShpalych Pro Bot
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Модуль для создания современных компонентов интерфейса Telegram бота.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

from bot_monitoring_service import DeviceInfo, DeviceStatus


@dataclass
class UIConfig:
    """Конфигурация UI компонентов"""
    max_button_text_length: int = 64
    progress_bar_width: int = 10
    table_column_width: int = 30
    max_devices_per_row: int = 3
    max_message_length: int = 3800


class UIIcons:
    """Централизованные иконки для UI"""
    # Статусы
    ONLINE = "🟢"
    OFFLINE = "🔴"
    CHECKING = "🟡"
    UNKNOWN = "⚪"
    
    # Действия
    REFRESH = "🔄"
    BACK = "🔙"
    HOME = "🏠"
    CHECK = "🔍"
    PING = "🎯"
    STATS = "📈"
    SETTINGS = "⚙️"
    HELP = "ℹ️"
    
    # Категории
    CENTRAL = "🏢"
    PASSAGE = "🚶"
    ESCALATOR = "🚇"
    TRANSITION = "🔄"
    ENTRANCE = "🚪"
    HALL = "🏛️"
    
    # Прогресс
    PROGRESS_FULL = "🟩"
    PROGRESS_EMPTY = "⬜"
    
    # Системные
    ROBOT = "🤖"
    ROCKET = "🚀"
    DEVICE = "📡"
    CLOCK = "⏰"
    CHART = "📊"
    LIST = "📋"
    BUILDING = "🏗️"


class KeyboardBuilder:
    """Строитель современных клавиатур с улучшенными возможностями"""
    
    def __init__(self, config: UIConfig = None):
        self.config = config or UIConfig()
        self.icons = UIIcons()
    
    def create_button(
        self, 
        text: str, 
        callback_data: str, 
        emoji: str = "",
        max_length: Optional[int] = None
    ) -> InlineKeyboardButton:
        """Создать стилизованную кнопку с автоматическим усечением"""
        max_len = max_length or self.config.max_button_text_length
        button_text = f"{emoji} {text}" if emoji else text
        
        if len(button_text) > max_len:
            button_text = button_text[:max_len-3] + "..."
        
        return InlineKeyboardButton(text=button_text, callback_data=callback_data)
    
    def create_keyboard(
        self, 
        buttons: List[List[InlineKeyboardButton]],
        adjust_width: bool = True
    ) -> InlineKeyboardMarkup:
        """Создать клавиатуру с оптимизированной компоновкой"""
        builder = InlineKeyboardBuilder()
        
        for row in buttons:
            if adjust_width and len(row) == 1:
                builder.row(*row, width=1)
            else:
                builder.row(*row)
        
        return builder.as_markup()
    
    def create_device_keyboard(
        self, 
        devices: List[DeviceInfo], 
        prefix: str = "device",
        max_per_row: Optional[int] = None
    ) -> List[List[InlineKeyboardButton]]:
        """Создать клавиатуру для списка устройств"""
        max_row = max_per_row or self.config.max_devices_per_row
        button_rows = []
        
        # Группируем устройства по max_per_row в ряд
        for i in range(0, len(devices), max_row):
            row = []
            for j in range(max_row):
                if i + j < len(devices):
                    device = devices[i + j]
                    button_text = device.id[:8] + "..." if len(device.id) > 8 else device.id
                    
                    status_emoji = self._get_device_status_emoji(device.status)
                    
                    row.append(self.create_button(
                        button_text, 
                        f"{prefix}_{device.id}", 
                        status_emoji
                    ))
            
            if row:
                button_rows.append(row)
        
        return button_rows
    
    def _get_device_status_emoji(self, status: Optional[str]) -> str:
        """Получить эмодзи статуса устройства"""
        if not status:
            return self.icons.UNKNOWN
        
        status_map = {
            DeviceStatus.ONLINE.value: self.icons.ONLINE,
            DeviceStatus.OFFLINE.value: self.icons.OFFLINE,
            DeviceStatus.CHECKING.value: self.icons.CHECKING,
            DeviceStatus.UNKNOWN.value: self.icons.UNKNOWN
        }
        
        return status_map.get(status, self.icons.UNKNOWN)


class MessageFormatter:
    """Форматировщик сообщений с улучшенным форматированием"""
    
    def __init__(self, config: UIConfig = None):
        self.config = config or UIConfig()
        self.icons = UIIcons()
    
    def format_device_status(self, device: DeviceInfo, show_details: bool = False) -> str:
        """Форматировать статус устройства с современными иконками"""
        status_emoji = self._get_status_emoji(device.status)
        base_text = f"{status_emoji} <b>{device.id}</b> • {device.ip}"
        
        if show_details:
            details = [
                f"📍 {device.location}",
                f"⏰ {self._format_time(device.last_check)}",
                f"📊 {self._format_response_time(device.response_time)}"
            ]
            base_text += f"\n{' | '.join(details)}"
        
        return base_text
    
    def create_progress_bar(
        self, 
        current: int, 
        total: int, 
        width: Optional[int] = None,
        show_percentage: bool = True
    ) -> str:
        """Создать улучшенную текстовую полосу прогресса"""
        width = width or self.config.progress_bar_width
        
        if total == 0:
            bar = self.icons.PROGRESS_EMPTY * width
            return f"{bar} 0.0%" if show_percentage else bar
        
        percentage = current / total
        filled = int(percentage * width)
        empty = width - filled
        
        bar = self.icons.PROGRESS_FULL * filled + self.icons.PROGRESS_EMPTY * empty
        
        if show_percentage:
            return f"{bar} {percentage*100:.1f}%"
        
        return bar
    
    def format_two_columns(
        self, 
        items: List[str], 
        col_width: Optional[int] = None,
        separator: str = "  "
    ) -> str:
        """Форматировать список строк в две колонки в <pre>"""
        if not items:
            return "<pre>—</pre>"
        
        col_width = col_width or self.config.table_column_width
        
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
            lines.append(f"{left_padded}{separator}{right_text}")
        
        return "<pre>" + "\n".join(lines) + "</pre>"
    
    def format_system_overview(
        self,
        total_devices: int,
        online_devices: int,
        offline_devices: int,
        categories_count: int,
        check_interval: int,
        user_id: Optional[int] = None
    ) -> str:
        """Форматировать обзор системы"""
        percentage = (online_devices / total_devices * 100) if total_devices > 0 else 0
        
        text = f"""
<b>{self.icons.ROBOT} TurboShpalych Pro - Система мониторинга турникетов</b>

<b>{self.icons.CHART} Обзор системы:</b>
├ {self.icons.DEVICE} Устройств: {total_devices}
├ {self.icons.ONLINE} Онлайн: {online_devices}
├ {self.icons.OFFLINE} Офлайн: {offline_devices}
├ {self.icons.CHART} Время работы: {percentage:.1f}%
└ {self.icons.BUILDING} Категорий: {categories_count}

<b>{self.icons.SETTINGS} Конфигурация:</b>
├ {self.icons.CLOCK} Интервал проверки: {check_interval}с
"""
        
        if user_id:
            text += f"├ 👤 Ваш ID: <code>{user_id}</code>\n"
        
        text += f"└ {self.icons.CLOCK} Время: {datetime.now().strftime('%H:%M:%S')}"
        
        return text
    
    def format_device_details(
        self,
        device: DeviceInfo,
        category_name: Optional[str] = None,
        category_icon: Optional[str] = None
    ) -> str:
        """Форматировать детальную информацию об устройстве"""
        status_emoji = self._get_status_emoji(device.status)
        
        text = f"""
{status_emoji} <b>{device.id}</b>

<b>📋 Информация:</b>
├ 🌐 IP: <code>{device.ip}</code>
├ 📍 Расположение: {device.location}
"""
        
        if category_name:
            cat_display = f"{category_icon} {category_name}" if category_icon else category_name
            text += f"├ 🏗️ Категория: {cat_display}\n"
        
        text += f"├ 📊 Статус: {device.status or 'Неизвестно'}\n"
        text += f"└ ⏰ Последняя проверка: {self._format_time(device.last_check)}"
        
        if device.response_time is not None:
            text += f"\n📈 Время отклика: {device.response_time:.1f}мс"
        
        return text
    
    def format_statistics_table(
        self,
        online_devices: List[DeviceInfo],
        offline_devices: List[DeviceInfo]
    ) -> Tuple[str, str]:
        """Форматировать таблицы статистики"""
        online_rows = [f"{d.id} — {d.ip}" for d in sorted(online_devices, key=lambda x: x.id)]
        offline_rows = [f"{d.id} — {d.ip}" for d in sorted(offline_devices, key=lambda x: x.id)]
        
        online_table = self.format_two_columns(online_rows)
        offline_table = self.format_two_columns(offline_rows)
        
        return online_table, offline_table
    
    def split_long_message(self, text: str, max_length: Optional[int] = None) -> List[str]:
        """Разделить длинное сообщение на части"""
        max_len = max_length or self.config.max_message_length
        
        if len(text) <= max_len:
            return [text]
        
        messages = []
        current_message = ""
        
        # Разделяем по абзацам
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_message) + len(paragraph) + 2 <= max_len:
                if current_message:
                    current_message += "\n\n" + paragraph
                else:
                    current_message = paragraph
            else:
                if current_message:
                    messages.append(current_message)
                current_message = paragraph
        
        if current_message:
            messages.append(current_message)
        
        return [msg for msg in messages if msg.strip()]
    
    def _get_status_emoji(self, status: Optional[str]) -> str:
        """Получить эмодзи статуса"""
        if not status:
            return self.icons.UNKNOWN
        
        status_map = {
            DeviceStatus.ONLINE.value: self.icons.ONLINE,
            DeviceStatus.OFFLINE.value: self.icons.OFFLINE,
            DeviceStatus.CHECKING.value: self.icons.CHECKING,
            DeviceStatus.UNKNOWN.value: self.icons.UNKNOWN
        }
        
        return status_map.get(status, self.icons.UNKNOWN)
    
    def _format_time(self, time_obj: Optional[datetime]) -> str:
        """Форматировать время"""
        if not time_obj:
            return "Никогда"
        return time_obj.strftime('%H:%M:%S')
    
    def _format_response_time(self, response_time: Optional[float]) -> str:
        """Форматировать время отклика"""
        if response_time is None:
            return "—"
        return f"{response_time:.1f}мс"


class UIComponents:
    """Основной класс UI компонентов, объединяющий все функциональность"""
    
    def __init__(self, config: UIConfig = None):
        self.config = config or UIConfig()
        self.icons = UIIcons()
        self.keyboard_builder = KeyboardBuilder(config)
        self.message_formatter = MessageFormatter(config)
    
    # Делегирование методов для обратной совместимости
    def create_button(self, text: str, callback_data: str, emoji: str = "") -> InlineKeyboardButton:
        return self.keyboard_builder.create_button(text, callback_data, emoji)
    
    def create_keyboard(self, buttons: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
        return self.keyboard_builder.create_keyboard(buttons)
    
    def format_device_status(self, device: DeviceInfo) -> str:
        return self.message_formatter.format_device_status(device)
    
    def create_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        return self.message_formatter.create_progress_bar(current, total, width)
    
    def format_two_columns(self, items: List[str], col_width: int = 28) -> str:
        return self.message_formatter.format_two_columns(items, col_width)