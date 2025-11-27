#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Error Handler for TurboShpalych Pro Bot
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Модуль для централизованной обработки ошибок и логирования.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
import json

from aiogram.exceptions import TelegramBadRequest, TelegramAPIError, TelegramNetworkError
from aiogram.types import Message, CallbackQuery


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Категории ошибок"""
    NETWORK = "network"
    TELEGRAM_API = "telegram_api"
    MONITORING = "monitoring"
    USER_INPUT = "user_input"
    SYSTEM = "system"
    CONFIGURATION = "configuration"


class StructuredLogger:
    """Структурированный логгер с дополнительными возможностями"""
    
    def __init__(self, name: str = __name__, log_file: str = 'bot.log'):
        self.logger = logging.getLogger(name)
        self.log_file = log_file
        
        # Настройка логгера если еще не настроен
        if not self.logger.handlers:
            self._setup_logger()
        
        # Callback для GUI логирования
        self.gui_callback: Optional[Callable[[str], None]] = None
        
        # Счетчики ошибок
        self.error_counts: Dict[str, int] = {}
        self.critical_errors: List[Dict[str, Any]] = []
    
    def _setup_logger(self):
        """Настроить логгер"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Файловый обработчик
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.setLevel(logging.INFO)
    
    def set_gui_callback(self, callback: Callable[[str], None]):
        """Установить callback для логирования в GUI"""
        self.gui_callback = callback
    
    def log_structured(
        self,
        level: str,
        message: str,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None
    ):
        """Записать структурированное сообщение"""
        # Формируем структурированное сообщение
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'category': category,
            'severity': severity,
            'user_id': user_id,
            'extra_data': extra_data or {}
        }
        
        if exception:
            log_entry['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        # Форматируем для обычного логгера
        formatted_message = self._format_log_message(log_entry)
        
        # Записываем в лог
        if level.upper() == 'ERROR':
            self.logger.error(formatted_message)
            self._count_error(category or 'unknown')
        elif level.upper() == 'WARNING':
            self.logger.warning(formatted_message)
        elif level.upper() == 'CRITICAL':
            self.logger.critical(formatted_message)
            self._store_critical_error(log_entry)
        else:
            self.logger.info(formatted_message)
        
        # Отправляем в GUI
        if self.gui_callback:
            gui_message = self._format_gui_message(log_entry)
            try:
                self.gui_callback(gui_message)
            except Exception as e:
                self.logger.error(f"Failed to send to GUI: {e}")
    
    def _format_log_message(self, log_entry: Dict[str, Any]) -> str:
        """Отформатировать сообщение для лог-файла"""
        parts = [log_entry['message']]
        
        if log_entry.get('category'):
            parts.append(f"[{log_entry['category']}]")
        
        if log_entry.get('user_id'):
            parts.append(f"[User:{log_entry['user_id']}]")
        
        if log_entry.get('severity'):
            parts.append(f"[Severity:{log_entry['severity']}]")
        
        if log_entry.get('extra_data'):
            extra_parts = [f"{k}={v}" for k, v in log_entry['extra_data'].items()]
            parts.append(f"[{', '.join(extra_parts)}]")
        
        return ' '.join(parts)
    
    def _format_gui_message(self, log_entry: Dict[str, Any]) -> str:
        """Отформатировать сообщение для GUI"""
        level_icons = {
            'ERROR': '❌',
            'WARNING': '⚠️',
            'CRITICAL': '🚨',
            'INFO': 'ℹ️'
        }
        
        icon = level_icons.get(log_entry['level'], '📝')
        message = f"{icon} {log_entry['message']}"
        
        if log_entry.get('category'):
            category_icons = {
                'network': '🌐',
                'telegram_api': '📱',
                'monitoring': '📊',
                'user_input': '👤',
                'system': '⚙️',
                'configuration': '🔧'
            }
            message += f" {category_icons.get(log_entry['category'], '📁')}"
        
        return message
    
    def _count_error(self, category: str):
        """Посчитать ошибку по категории"""
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
    
    def _store_critical_error(self, log_entry: Dict[str, Any]):
        """Сохранить критическую ошибку"""
        self.critical_errors.append(log_entry)
        
        # Ограничиваем количество сохраненных ошибок
        if len(self.critical_errors) > 50:
            self.critical_errors = self.critical_errors[-25:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Получить сводку ошибок"""
        return {
            'error_counts': self.error_counts.copy(),
            'critical_errors_count': len(self.critical_errors),
            'recent_critical_errors': self.critical_errors[-5:] if self.critical_errors else []
        }
    
    def clear_error_counts(self):
        """Очистить счетчики ошибок"""
        self.error_counts.clear()
        self.critical_errors.clear()


class ErrorHandler:
    """Централизованный обработчик ошибок"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 30.0,
            'exponential_base': 2.0
        }
        
        # Статистика обработки ошибок
        self.handled_errors = 0
        self.retries_attempted = 0
        self.retries_successful = 0
    
    async def handle_telegram_error(
        self,
        error: Exception,
        message_or_callback: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Обработать ошибку Telegram API"""
        context = context or {}
        user_id = None
        
        if isinstance(message_or_callback, Message):
            user_id = message_or_callback.from_user.id
            message_type = 'message'
            message_id = message_or_callback.message_id
        elif isinstance(message_or_callback, CallbackQuery):
            user_id = message_or_callback.from_user.id
            message_type = 'callback'
            message_id = message_or_callback.message.message_id
        else:
            message_type = 'unknown'
            message_id = None
        
        # Определяем тип ошибки
        if isinstance(error, TelegramBadRequest):
            category = ErrorCategory.TELEGRAM_API
            severity = ErrorSeverity.MEDIUM
            
            # Специальная обработка для常见 ошибок
            error_message = str(error).lower()
            
            if "chat not found" in error_message:
                await self._handle_chat_not_found(user_id, context)
            elif "message to edit not found" in error_message:
                await self._handle_message_not_found(message_or_callback, context)
            elif "message is too long" in error_message:
                await self._handle_message_too_long(message_or_callback, context)
            elif "too many requests" in error_message:
                await self._handle_rate_limit(message_or_callback, context)
            
        elif isinstance(error, TelegramNetworkError):
            category = ErrorCategory.NETWORK
            severity = ErrorSeverity.HIGH
        elif isinstance(error, TelegramAPIError):
            category = ErrorCategory.TELEGRAM_API
            severity = ErrorSeverity.HIGH
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.CRITICAL
        
        # Логируем ошибку
        self.logger.log_structured(
            level='ERROR',
            message=f"Telegram error: {type(error).__name__}: {str(error)}",
            category=category.value,
            severity=severity.value,
            user_id=user_id,
            extra_data={
                'message_type': message_type,
                'message_id': message_id,
                **context
            },
            exception=error
        )
        
        self.handled_errors += 1
        
        # Возвращаем True если ошибку можно обработать и продолжить
        return severity != ErrorSeverity.CRITICAL
    
    async def handle_monitoring_error(
        self,
        error: Exception,
        device_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Обработать ошибку мониторинга"""
        context = context or {}
        
        self.logger.log_structured(
            level='ERROR',
            message=f"Monitoring error for device {device_id}: {str(error)}",
            category=ErrorCategory.MONITORING.value,
            severity=ErrorSeverity.MEDIUM.value,
            extra_data={
                'device_id': device_id,
                **context
            },
            exception=error
        )
        
        self.handled_errors += 1
        
        # Для ошибок мониторинга обычно можно продолжать работу
        return True
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Выполнить функцию с повторными попытками"""
        max_retries = max_retries or self.retry_config['max_retries']
        context = context or {}
        
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                self.retries_attempted += 1
                
                if attempt == max_retries:
                    # Последняя попытка неудачна
                    self.logger.log_structured(
                        level='ERROR',
                        message=f"Failed after {max_retries + 1} attempts: {str(e)}",
                        category=ErrorCategory.SYSTEM.value,
                        severity=ErrorSeverity.HIGH.value,
                        extra_data={
                            'attempts': max_retries + 1,
                            'function': func.__name__,
                            **context
                        },
                        exception=e
                    )
                    raise
                
                # Рассчитываем задержку
                delay = min(
                    self.retry_config['base_delay'] * (self.retry_config['exponential_base'] ** attempt),
                    self.retry_config['max_delay']
                )
                
                self.logger.log_structured(
                    level='WARNING',
                    message=f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}",
                    category=ErrorCategory.SYSTEM.value,
                    severity=ErrorSeverity.LOW.value,
                    extra_data={
                        'attempt': attempt + 1,
                        'delay': delay,
                        'function': func.__name__,
                        **context
                    }
                )
                
                await asyncio.sleep(delay)
        
        # Этот код не должен достигаться
        raise RuntimeError("Unexpected error in retry logic")
    
    async def safe_message_edit(
        self,
        message: Message,
        text: str,
        reply_markup=None,
        parse_mode=None
    ) -> bool:
        """Безопасное редактирование сообщения с обработкой ошибок"""
        try:
            await message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        
        except Exception as e:
            await self.handle_telegram_error(
                error=e,
                message_or_callback=message,
                context={
                    'operation': 'edit_text',
                    'text_length': len(text),
                    'has_reply_markup': reply_markup is not None,
                    'parse_mode': parse_mode
                }
            )
            
            # Пытаемся отправить новое сообщение если редактирование не удалось
            try:
                await message.answer(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return True
            except Exception as e2:
                await self.handle_telegram_error(
                    error=e2,
                    message_or_callback=message,
                    context={'operation': 'fallback_answer'}
                )
                return False
    
    async def safe_callback_answer(
        self,
        callback: CallbackQuery,
        text: str = "",
        show_alert: bool = False,
        cache_time: Optional[int] = None
    ) -> bool:
        """Безопасный ответ на callback с обработкой ошибок"""
        try:
            await callback.answer(
                text=text,
                show_alert=show_alert,
                cache_time=cache_time
            )
            return True
        
        except Exception as e:
            await self.handle_telegram_error(
                error=e,
                message_or_callback=callback,
                context={
                    'operation': 'callback_answer',
                    'text': text,
                    'show_alert': show_alert,
                    'cache_time': cache_time
                }
            )
            return False
    
    async def _handle_chat_not_found(self, user_id: Optional[int], context: Dict[str, Any]):
        """Обработать ошибку 'chat not found'"""
        self.logger.log_structured(
            level='WARNING',
            message=f"Chat not found for user {user_id}",
            category=ErrorCategory.TELEGRAM_API.value,
            severity=ErrorSeverity.MEDIUM.value,
            user_id=user_id
        )
    
    async def _handle_message_not_found(self, message_or_callback: Any, context: Dict[str, Any]):
        """Обработать ошибку 'message to edit not found'"""
        # Это обычно не критичная ошибка, просто логируем
        pass
    
    async def _handle_message_too_long(self, message_or_callback: Any, context: Dict[str, Any]):
        """Обработать ошибку 'message is too long'"""
        self.logger.log_structured(
            level='WARNING',
            message="Message too long, needs truncation",
            category=ErrorCategory.USER_INPUT.value,
            severity=ErrorSeverity.LOW.value
        )
    
    async def _handle_rate_limit(self, message_or_callback: Any, context: Dict[str, Any]):
        """Обработать ошибку 'too many requests'"""
        self.logger.log_structured(
            level='WARNING',
            message="Rate limit exceeded",
            category=ErrorCategory.TELEGRAM_API.value,
            severity=ErrorSeverity.MEDIUM.value
        )
        
        # Добавляем небольшую задержку
        await asyncio.sleep(1.0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику обработчика ошибок"""
        return {
            'handled_errors': self.handled_errors,
            'retries_attempted': self.retries_attempted,
            'retries_successful': self.retries_successful,
            'retry_success_rate': (
                self.retries_successful / self.retries_attempted * 100
                if self.retries_attempted > 0 else 0
            )
        }


# Глобальный экземпляр логгера и обработчика ошибок
structured_logger = StructuredLogger()
error_handler = ErrorHandler(structured_logger)