#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FSM Handlers for TurboShpalych Pro Bot
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Модуль для обработки состояний пользователя и обратных вызовов.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from aiogram import F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot_ui_components import UIComponents, UIIcons
from bot_monitoring_service import DeviceInfo, DeviceStatus, MonitoringStats
from bot_error_handler import error_handler, structured_logger


class UserStates(StatesGroup):
    """Состояния взаимодействия пользователя"""
    main_menu = State()
    viewing_category = State()
    viewing_device = State()
    waiting_input = State()


class FSMHandlers:
    """Обработчики состояний и обратных вызовов"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.ui = UIComponents()
        self.icons = UIIcons()
        
        # Кэш для быстрого доступа к данным
        self._stats_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 30.0  # seconds
    
    def register_all_handlers(self, dp):
        """Зарегистрировать все обработчики"""
        # Обработчики команд
        dp.message.register(self.cmd_start, CommandStart())
        dp.message.register(self.cmd_help, Command('help'))
        dp.message.register(self.cmd_stats, Command('stats'))
        
        # Обработчики обратных вызовов с паттернами
        self._register_callback_handlers(dp)
    
    def _register_callback_handlers(self, dp):
        """Зарегистрировать обработчики обратных вызовов"""
        # Основные навигационные обработчики
        dp.callback_query.register(self.handle_main_menu, F.data == "main_menu")
        dp.callback_query.register(self.handle_system_status, F.data == "system_status")
        dp.callback_query.register(self.handle_statistics, F.data == "statistics")
        dp.callback_query.register(self.handle_all_devices, F.data == "all_devices")
        dp.callback_query.register(self.handle_online_devices, F.data == "online_devices")
        dp.callback_query.register(self.handle_offline_devices, F.data == "offline_devices")
        dp.callback_query.register(self.handle_categories, F.data == "categories")
        dp.callback_query.register(self.handle_device_ping_menu, F.data == "device_ping_menu")
        dp.callback_query.register(self.handle_help, F.data == "help")
        
        # Динамические паттерны обратных вызовов
        dp.callback_query.register(
            self.handle_category_view, 
            F.data.startswith("cat_")
        )
        dp.callback_query.register(
            self.handle_device_check, 
            F.data.startswith("device_")
        )
        dp.callback_query.register(
            self.handle_device_ping, 
            F.data.startswith("ping_")
        )
        dp.callback_query.register(
            self.handle_refresh, 
            F.data.startswith("refresh_")
        )
    
    # ============= Обработчики команд =============
    
    async def cmd_start(self, message: Message, state: FSMContext):
        """Обработать команду /start"""
        await state.set_state(UserStates.main_menu)
        
        user_info = self._extract_user_info(message.from_user)
        
        # Детальное логирование
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} sent /start command",
            category='user_input',
            user_id=user_info['id'],
            extra_data=user_info
        )
        
        keyboard = self._create_main_menu_keyboard()
        stats = await self._get_cached_stats()
        
        welcome_text = self.ui.message_formatter.format_system_overview(
            total_devices=stats.total,
            online_devices=stats.online,
            offline_devices=stats.offline,
            categories_count=len(self.bot.categories),
            check_interval=self.bot.time_connect,
            user_id=message.from_user.id
        )
        
        welcome_text += "\n\nВыберите действие ниже:"
        
        await message.answer(
            welcome_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Main menu sent to user {user_info['name']}",
            category='user_input',
            user_id=user_info['id']
        )
    
    async def cmd_help(self, message: Message):
        """Обработать команду /help"""
        await self._send_help_message(message)
    
    async def cmd_stats(self, message: Message):
        """Обработать команду /stats"""
        await self._send_statistics_message(message)
    
    # ============= Обработчики обратных вызовов =============
    
    async def handle_main_menu(self, callback: CallbackQuery, state: FSMContext):
        """Обработать обратный вызов главного меню"""
        user_info = self._extract_user_info(callback.from_user)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} pressed 'Main Menu'",
            category='user_input',
            user_id=user_info['id']
        )
        
        await state.set_state(UserStates.main_menu)
        await self._show_main_menu(callback.message)
        await error_handler.safe_callback_answer(callback)
    
    async def handle_system_status(self, callback: CallbackQuery):
        """Обработать запрос статуса системы"""
        user_info = self._extract_user_info(callback.from_user)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} requested system status",
            category='user_input',
            user_id=user_info['id']
        )
        
        await error_handler.safe_callback_answer(callback, "🔄 Checking system status...")
        await self._show_system_status(callback.message)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"System status sent to {user_info['name']}",
            category='user_input',
            user_id=user_info['id']
        )
    
    async def handle_statistics(self, callback: CallbackQuery):
        """Обработать запрос статистики"""
        user_info = self._extract_user_info(callback.from_user)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} requested statistics",
            category='user_input',
            user_id=user_info['id']
        )
        
        await error_handler.safe_callback_answer(callback, "📊 Loading statistics...")
        await self._send_statistics_message(callback.message)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Statistics sent to {user_info['name']}",
            category='user_input',
            user_id=user_info['id']
        )
    
    async def handle_all_devices(self, callback: CallbackQuery):
        """Обработать просмотр всех устройств"""
        await error_handler.safe_callback_answer(callback, "📋 Loading all devices...")
        await self._show_all_devices(callback.message)
    
    async def handle_online_devices(self, callback: CallbackQuery):
        """Обработать просмотр онлайн устройств"""
        await error_handler.safe_callback_answer(callback, "🟢 Loading online devices...")
        await self._show_filtered_devices(callback.message, DeviceStatus.ONLINE)
    
    async def handle_offline_devices(self, callback: CallbackQuery):
        """Обработать просмотр офлайн устройств"""
        await error_handler.safe_callback_answer(callback, "🔴 Loading offline devices...")
        await self._show_filtered_devices(callback.message, DeviceStatus.OFFLINE)
    
    async def handle_categories(self, callback: CallbackQuery):
        """Обработать просмотр категорий"""
        await error_handler.safe_callback_answer(callback, "🏗️ Loading categories...")
        await self._show_categories(callback.message)
    
    async def handle_help(self, callback: CallbackQuery):
        """Обработать запрос помощи"""
        await error_handler.safe_callback_answer(callback)
        await self._send_help_message(callback.message)
    
    async def handle_device_ping_menu(self, callback: CallbackQuery):
        """Показать меню пинга устройств"""
        await error_handler.safe_callback_answer(callback, "Loading ping menu...")
        
        devices = list(self.bot.devices.values())
        device_buttons = self.ui.keyboard_builder.create_device_keyboard(
            devices, prefix="ping", max_per_row=4
        )
        
        # Добавляем кнопки навигации
        device_buttons.append([
            self.ui.create_button("Back", "main_menu", self.icons.BACK)
        ])
        
        keyboard = self.ui.create_keyboard(device_buttons)
        
        text = f"""
<b>{self.icons.PING} Device Ping Menu</b>

Select a device to check connection:
📱 Total devices: {len(devices)}

💡 <i>Click on device button to perform ping</i>
"""
        
        await error_handler.safe_message_edit(
            callback.message,
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    async def handle_device_ping(self, callback: CallbackQuery):
        """Обработать пинг конкретного устройства"""
        device_id = callback.data.replace("ping_", "")
        user_info = self._extract_user_info(callback.from_user)
        
        await error_handler.safe_callback_answer(
            callback, f"{self.icons.PING} Pinging {device_id}..."
        )
        
        if device_id not in self.bot.devices:
            await error_handler.safe_message_edit(
                callback.message,
                f"❌ Device not found!"
            )
            return
        
        device = self.bot.devices[device_id]
        
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} pinged device {device_id}",
            category='user_input',
            user_id=user_info['id'],
            extra_data={'device_id': device_id, 'device_ip': device.ip}
        )
        
        # Выполняем проверку устройства
        try:
            updated_device = await error_handler.execute_with_retry(
                self.bot.monitoring_service.check_device,
                device,
                use_cache=False,
                force_refresh=True,
                context={'operation': 'manual_ping'}
            )
        except Exception as e:
            await error_handler.handle_monitoring_error(e, device_id, {'operation': 'manual_ping'})
            await error_handler.safe_message_edit(
                callback.message,
                f"❌ Error checking device {device_id}"
            )
            return
        
        # Обновляем устройство в боте
        self.bot.devices[device_id] = updated_device
        
        # Формируем ответ
        response_text = self._format_ping_result(updated_device, user_info['name'])
        
        # Создаем кнопки для дальнейших действий
        action_buttons = [
            [
                self.ui.create_button("Retry", f"ping_{device_id}", self.icons.REFRESH),
                self.ui.create_button("Back to List", "device_ping_menu", self.icons.BACK)
            ],
            [
                self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)
            ]
        ]
        
        keyboard = self.ui.create_keyboard(action_buttons)
        
        await error_handler.safe_message_edit(
            callback.message,
            response_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def handle_category_view(self, callback: CallbackQuery, state: FSMContext):
        """Обработать просмотр устройств категории"""
        category_id = callback.data.replace("cat_", "")
        
        await state.set_state(UserStates.viewing_category)
        await state.update_data(category_id=category_id)
        await error_handler.safe_callback_answer(
            callback, f"Loading category {category_id}..."
        )
        await self._show_category_devices(callback.message, category_id)
    
    async def handle_device_check(self, callback: CallbackQuery, state: FSMContext):
        """Обработать проверку одного устройства"""
        user_info = self._extract_user_info(callback.from_user)
        device_id = callback.data.replace("device_", "")
        
        structured_logger.log_structured(
            level='INFO',
            message=f"User {user_info['name']} requested device check: {device_id}",
            category='user_input',
            user_id=user_info['id'],
            extra_data={'device_id': device_id}
        )
        
        await state.set_state(UserStates.viewing_device)
        await state.update_data(device_id=device_id)
        await error_handler.safe_callback_answer(
            callback, f"{self.icons.CHECK} Checking {device_id}..."
        )
        await self._check_single_device(callback.message, device_id)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Device {device_id} checked for {user_info['name']}",
            category='user_input',
            user_id=user_info['id']
        )
    
    async def handle_refresh(self, callback: CallbackQuery):
        """Обработать действие обновления"""
        action = callback.data.replace("refresh_", "")
        await error_handler.safe_callback_answer(callback, f"{self.icons.REFRESH} Refreshing...")
        
        if action == "status":
            await self._show_system_status(callback.message)
        elif action == "all":
            await self._show_all_devices(callback.message)
        elif action in ("онлайн", "офлайн"):
            await self._show_filtered_devices(
                callback.message,
                DeviceStatus.ONLINE if action == "онлайн" else DeviceStatus.OFFLINE
            )
        elif action.startswith("device_"):
            device_id = action.replace("device_", "")
            await self._check_single_device(callback.message, device_id)
    
    # ============= Приватные методы интерфейса =============
    
    def _create_main_menu_keyboard(self):
        """Создать клавиатуру главного меню"""
        return self.ui.create_keyboard([
            [
                self.ui.create_button("System Status", "system_status", self.icons.CHART),
                self.ui.create_button("Statistics", "statistics", self.icons.STATS)
            ],
            [
                self.ui.create_button("Online", "online_devices", self.icons.ONLINE),
                self.ui.create_button("Offline", "offline_devices", self.icons.OFFLINE)
            ],
            [
                self.ui.create_button("All Devices", "all_devices", self.icons.LIST),
                self.ui.create_button("Categories", "categories", self.icons.BUILDING)
            ],
            [
                self.ui.create_button("Ping Devices", "device_ping_menu", self.icons.PING)
            ],
            [
                self.ui.create_button("Help", "help", self.icons.HELP)
            ]
        ])
    
    async def _show_main_menu(self, message: Message):
        """Показать главное меню"""
        keyboard = self._create_main_menu_keyboard()
        stats = await self._get_cached_stats()
        
        text = f"""
<b>{self.icons.ROBOT} TurboShpalych Pro - Main Menu</b>

<b>{self.icons.CHART} Quick Statistics:</b>
{self.ui.create_progress_bar(stats.online, stats.total)} {stats.percentage:.1f}%

├ {self.icons.DEVICE} Total: {stats.total}
├ {self.icons.ONLINE} Online: {stats.online}
├ {self.icons.OFFLINE} Offline: {stats.offline}
└ {self.icons.BUILDING} Categories: {len(self.bot.categories)}

Select an option:
"""
        
        await error_handler.safe_message_edit(
            message,
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _show_system_status(self, message: Message):
        """Показать детальный статус системы"""
        # Показать сообщение загрузки
        loading_msg = await error_handler.safe_message_edit(
            message,
            f"🔄 <b>Analyzing system status...</b>",
            parse_mode="HTML"
        )
        
        # Проверить все устройства
        devices_list = list(self.bot.devices.values())
        checked_devices = await error_handler.execute_with_retry(
            self.bot.monitoring_service.check_multiple_devices,
            devices_list,
            use_cache=False,
            force_refresh=True,
            context={'operation': 'system_status_check'}
        )
        
        # Обновить статус устройств
        for device in checked_devices:
            self.bot.devices[device.id] = device
        
        stats = self.bot.monitoring_service.get_statistics(checked_devices)
        
        # Две колонки: список всех устройств
        rows = [
            f"{self._get_device_emoji(d.status)} {d.id} — {d.ip}" 
            for d in sorted(checked_devices, key=lambda x: x.id)
        ]
        table = self.ui.format_two_columns(rows, col_width=30)
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Refresh", "refresh_status", self.icons.REFRESH)],
            [
                self.ui.create_button("Main Menu", "main_menu", self.icons.HOME),
                self.ui.create_button("Details", "all_devices", self.icons.LIST)
            ]
        ])
        
        status_text = f"""
<b>{self.icons.CHART} System Status Report</b>

<b>{self.icons.CHART} Overall Status:</b>
{self.ui.create_progress_bar(stats.online, stats.total)} {stats.percentage:.1f}%

<b>{self.icons.STATS} Statistics:</b>
├ {self.icons.DEVICE} Total devices: {stats.total}
├ {self.icons.ONLINE} Online: {stats.online} ({stats.online/stats.total*100:.1f}%)
├ {self.icons.OFFLINE} Offline: {stats.offline} ({stats.offline/stats.total*100:.1f}%)
└ {self.icons.CLOCK} Check interval: {self.bot.time_connect}s

<b>{self.icons.LIST} Devices:</b>
{table}

<b>{self.icons.CLOCK} Last update:</b> {stats.last_update.strftime('%H:%M:%S')}
"""
        
        await error_handler.safe_message_edit(
            loading_msg,
            status_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _show_all_devices(self, message: Message):
        """Показать все устройства с их статусом"""
        loading_msg = await error_handler.safe_message_edit(
            message,
            f"🔄 <b>Checking all devices...</b>",
            parse_mode="HTML"
        )
        
        # Проверить все устройства
        devices_list = list(self.bot.devices.values())
        checked_devices = await error_handler.execute_with_retry(
            self.bot.monitoring_service.check_multiple_devices,
            devices_list,
            use_cache=False,
            force_refresh=True,
            context={'operation': 'all_devices_check'}
        )
        
        # Обновить локальные статусы устройств
        for device in checked_devices:
            self.bot.devices[device.id] = device
        
        # Полный список в две колонки
        rows = [
            f"{self._get_device_emoji(d.status)} {d.id} — {d.ip}" 
            for d in sorted(checked_devices, key=lambda x: x.id)
        ]
        table = self.ui.format_two_columns(rows, col_width=30)
        
        stats = self.bot.monitoring_service.get_statistics(checked_devices)
        output_lines = [
            f"<b>{self.icons.LIST} All Devices Status</b>", 
            table, 
            f"<b>{self.icons.CHART} Total:</b> {self.icons.ONLINE} {stats.online} | {self.icons.OFFLINE} {stats.offline}"
        ]
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Refresh", "refresh_all", self.icons.REFRESH)],
            [
                self.ui.create_button("Online Only", "online_devices", self.icons.ONLINE),
                self.ui.create_button("Offline Only", "offline_devices", self.icons.OFFLINE)
            ],
            [self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)]
        ])
        
        await error_handler.safe_message_edit(
            loading_msg,
            "\n".join(output_lines),
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _show_filtered_devices(self, message: Message, status_filter: DeviceStatus):
        """Показать устройства, отфильтрованные по статусу"""
        status_emoji = self.icons.ONLINE if status_filter == DeviceStatus.ONLINE else self.icons.OFFLINE
        
        loading_msg = await error_handler.safe_message_edit(
            message,
            f"🔄 <b>Checking {status_filter.value} devices...</b>",
            parse_mode="HTML"
        )
        
        # Проверить все устройства
        devices_list = list(self.bot.devices.values())
        checked_devices = await error_handler.execute_with_retry(
            self.bot.monitoring_service.check_multiple_devices,
            devices_list,
            use_cache=False,
            force_refresh=True,
            context={'operation': f'{status_filter.value}_devices_check'}
        )
        
        # Обновить локальные статусы устройств
        for device in checked_devices:
            self.bot.devices[device.id] = device
        
        # Отфильтровать устройства
        filtered = [d for d in checked_devices if d.status == status_filter.value]
        header = f"<b>{status_emoji} {status_filter.value.title()} Devices ({len(filtered)})</b>"
        rows = [f"{d.id} — {d.ip}" for d in sorted(filtered, key=lambda x: x.id)]
        table = self.ui.format_two_columns(rows, col_width=30)
        text = header + "\n" + table
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Refresh", f"refresh_{status_filter.value}", self.icons.REFRESH)],
            [self.ui.create_button("All Devices", "all_devices", self.icons.LIST)],
            [self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)]
        ])
        
        await error_handler.safe_message_edit(
            loading_msg,
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _show_categories(self, message: Message):
        """Показать категории устройств"""
        # Создать кнопки категорий
        button_rows = []
        for cat_id, cat_info in self.bot.categories.items():
            button = self.ui.create_button(
                f"{cat_info.name} ({len(cat_info.devices)})",
                f"cat_{cat_id}",
                cat_info.icon
            )
            button_rows.append([button])
        
        button_rows.append([self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)])
        
        keyboard = self.ui.create_keyboard(button_rows)
        
        text = f"""
<b>{self.icons.BUILDING} Device Categories</b>

Select a category to view devices:

<b>{self.icons.CHART} Categories Overview:</b>
"""
        for cat_id, cat_info in self.bot.categories.items():
            text += f"\n{cat_info.icon} <b>{cat_info.name}:</b> {len(cat_info.devices)} devices"
        
        text += f"\n\n<b>Total:</b> {len(self.bot.devices)} devices in {len(self.bot.categories)} categories"
        
        await error_handler.safe_message_edit(
            message,
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _show_category_devices(self, message: Message, category_id: str):
        """Показать устройства в конкретной категории"""
        if category_id not in self.bot.categories:
            await error_handler.safe_message_edit(message, "❌ Category not found")
            return
        
        cat_info = self.bot.categories[category_id]
        devices = [self.bot.devices[d_id] for d_id in cat_info.devices if d_id in self.bot.devices]
        
        # Проверить устройства
        loading_msg = await error_handler.safe_message_edit(
            message,
            f"🔄 <b>Checking {cat_info.name} devices...</b>",
            parse_mode="HTML"
        )
        
        checked_devices = await error_handler.execute_with_retry(
            self.bot.monitoring_service.check_multiple_devices,
            devices,
            use_cache=False,
            force_refresh=True,
            context={'operation': 'category_devices_check', 'category': category_id}
        )
        
        # Форматировать вывод
        lines = [f"{cat_info.icon} <b>{cat_info.name}</b>\n"]
        
        for device in checked_devices:
            lines.append(self.ui.format_device_status(device))
            lines.append(f"  📍 {device.location}\n")
        
        stats = self.bot.monitoring_service.get_statistics(checked_devices)
        lines.append(f"<b>{self.icons.CHART} Total:</b> {self.icons.ONLINE} {stats.online} | {self.icons.OFFLINE} {stats.offline}")
        
        # Создать кнопки проверки устройств
        button_rows = []
        for device in checked_devices[:6]:  # Ограничить кнопки
            button = self.ui.create_button(
                device.id,
                f"device_{device.id}",
                self.icons.CHECK
            )
            button_rows.append([button])
        
        button_rows.append([
            self.ui.create_button("Categories", "categories", self.icons.BUILDING),
            self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)
        ])
        
        keyboard = self.ui.create_keyboard(button_rows)
        
        await error_handler.safe_message_edit(
            loading_msg,
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _check_single_device(self, message: Message, device_id: str):
        """Проверить детальный статус одного устройства"""
        if device_id not in self.bot.devices:
            await error_handler.safe_message_edit(message, "❌ Device not found")
            return
        
        device = self.bot.devices[device_id]
        
        # Проверить устройство
        loading_msg = await error_handler.safe_message_edit(
            message,
            f"🔍 <b>Checking {device_id}...</b>",
            parse_mode="HTML"
        )
        
        try:
            checked_device = await error_handler.execute_with_retry(
                self.bot.monitoring_service.check_device,
                device,
                use_cache=False,
                force_refresh=True,
                context={'operation': 'single_device_check'}
            )
        except Exception as e:
            await error_handler.handle_monitoring_error(e, device_id, {'operation': 'single_device_check'})
            await error_handler.safe_message_edit(
                loading_msg,
                f"❌ Error checking device {device_id}"
            )
            return
        
        self.bot.devices[device_id] = checked_device
        
        # Форматировать детальную информацию
        cat_info = self.bot.categories.get(checked_device.category, None)
        
        text = self.ui.message_formatter.format_device_details(
            checked_device,
            cat_info.name if cat_info else None,
            cat_info.icon if cat_info else None
        )
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Check Again", f"refresh_device_{device_id}", self.icons.REFRESH)],
            [
                self.ui.create_button("Category", f"cat_{checked_device.category}", self.icons.BUILDING),
                self.ui.create_button("All Devices", "all_devices", self.icons.LIST)
            ],
            [self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)]
        ])
        
        await error_handler.safe_message_edit(
            loading_msg,
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _send_help_message(self, message: Message):
        """Отправить сообщение помощи"""
        help_text = f"""
<b>{self.icons.HELP} TurboShpalych Pro Help</b>

<b>{self.icons.ROBOT} Features:</b>
• Real-time device monitoring
• Category organization
• Detailed statistics
• Quick status checks

<b>{self.icons.ROBOT} Commands:</b>
• /start - Main menu
• /help - This help message
• /stats - Quick statistics

<b>{self.icons.BUILDING} Categories:</b>
• Each device organized by type
• Quick access to related devices
• Batch status checks

<b>{self.icons.HELP} Tips:</b>
• Use {self.icons.REFRESH} to refresh data
• Click device names for details
• Check categories for group viewing

<b>{self.icons.ROBOT} Your ID:</b> <code>{message.from_user.id if hasattr(message, 'from_user') else message.chat.id}</code>

<b>{self.icons.SETTINGS} System:</b> Shpalych Edition
"""
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)]
        ])
        
        await error_handler.safe_message_edit(
            message,
            help_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    async def _send_statistics_message(self, message: Message):
        """Отправить детальную статистику"""
        # Проверить все устройства для свежей статистики
        devices_list = list(self.bot.devices.values())
        checked_devices = await error_handler.execute_with_retry(
            self.bot.monitoring_service.check_multiple_devices,
            devices_list,
            use_cache=False,
            force_refresh=True,
            context={'operation': 'statistics_check'}
        )
        
        stats = self.bot.monitoring_service.get_statistics(checked_devices)
        online_list = [d for d in checked_devices if d.status == DeviceStatus.ONLINE.value]
        offline_list = [d for d in checked_devices if d.status == DeviceStatus.OFFLINE.value]
        
        online_table, offline_table = self.ui.message_formatter.format_statistics_table(
            online_list, offline_list
        )
        
        text = f"""
<b>{self.icons.STATS} Detailed Statistics</b>

<b>{self.icons.CHART} Overall Performance:</b>
{self.ui.create_progress_bar(stats.online, stats.total)} {stats.percentage:.1f}%

<b>{self.icons.STATS} General Statistics:</b>
├ {self.icons.DEVICE} Total devices: {stats.total}
├ {self.icons.ONLINE} Online: {stats.online} ({stats.percentage:.1f}%)
├ {self.icons.OFFLINE} Offline: {stats.offline} ({100 - stats.percentage:.1f}%)
└ {self.icons.CLOCK} Check interval: {self.bot.time_connect}s

<b>{self.icons.ONLINE} Online:</b>
{online_table}

<b>{self.icons.OFFLINE} Offline:</b>
{offline_table}

<b>{self.icons.CLOCK} Generated:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        
        keyboard = self.ui.create_keyboard([
            [self.ui.create_button("Refresh", "statistics", self.icons.REFRESH)],
            [self.ui.create_button("Main Menu", "main_menu", self.icons.HOME)]
        ])
        
        await error_handler.safe_message_edit(
            message,
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    # ============= Вспомогательные методы =============
    
    def _extract_user_info(self, user) -> Dict[str, Any]:
        """Извлечь информацию о пользователе"""
        return {
            'id': user.id,
            'name': user.full_name or "Unknown",
            'username': user.username or "no_username"
        }
    
    def _get_device_emoji(self, status: Optional[str]) -> str:
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
    
    def _format_ping_result(self, device: DeviceInfo, user_name: str) -> str:
        """Форматировать результат пинга"""
        status_emoji = self._get_device_emoji(device.status)
        status_text = device.status.upper() if device.status else "UNKNOWN"
        
        return f"""
{status_emoji} <b>Ping Result</b>

📍 <b>Device:</b> {device.id}
🌐 <b>IP:</b> <code>{device.ip}</code>
📍 <b>Location:</b> {device.location}
{status_emoji} <b>Status:</b> {status_text}
⏰ <b>Check time:</b> {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}

{'✅ Device is responding!' if device.status == DeviceStatus.ONLINE.value else '❌ Device is not responding!'}
"""
    
    async def _get_cached_stats(self) -> MonitoringStats:
        """Получить кэшированную статистику"""
        now = datetime.now()
        
        # Проверяем актуальность кэша
        if (self._cache_timestamp is None or 
            (now - self._cache_timestamp).total_seconds() > self._cache_ttl):
            
            # Обновляем кэш
            devices_list = list(self.bot.devices.values())
            checked_devices = await self.bot.monitoring_service.check_multiple_devices(
                devices_list, use_cache=True
            )
            
            self._stats_cache = self.bot.monitoring_service.get_statistics(checked_devices)
            self._cache_timestamp = now
        
        return self._stats_cache