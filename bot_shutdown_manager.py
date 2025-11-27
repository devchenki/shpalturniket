#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shutdown Manager for TurboShpalych Pro Bot
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Модуль для управления грациозным завершением работы бота.
"""

import asyncio
import signal
import logging
from datetime import datetime
from typing import Set, List, Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum

from bot_error_handler import structured_logger


class ShutdownReason(Enum):
    """Причины завершения работы"""
    SIGNAL_INTERRUPT = "signal_interrupt"
    SIGNAL_TERMINATE = "signal_terminate"
    CRITICAL_ERROR = "critical_error"
    USER_REQUEST = "user_request"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class ShutdownTask:
    """Задача для выполнения при завершении работы"""
    name: str
    func: Callable
    priority: int  # 0 = высший приоритет
    timeout: float = 30.0
    critical: bool = False  # Если True, ошибка прерывает завершение


class ShutdownManager:
    """Менеджер грациозного завершения работы"""
    
    def __init__(self):
        self.shutdown_tasks: List[ShutdownTask] = []
        self.running_tasks: Set[asyncio.Task] = set()
        self.is_shutting_down = False
        self.shutdown_reason: Optional[ShutdownReason] = None
        self.shutdown_start_time: Optional[datetime] = None
        self.shutdown_timeout = 60.0  # Общий таймаут завершения
        
        # Сигналы для отслеживания
        self.shutdown_event = asyncio.Event()
        self.completion_event = asyncio.Event()
        
        # Коллбэки
        self.before_shutdown_callbacks: List[Callable] = []
        self.after_shutdown_callbacks: List[Callable] = []
        
        # Статистика
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.skipped_tasks = 0
    
    def register_task(
        self,
        name: str,
        func: Callable,
        priority: int = 10,
        timeout: float = 30.0,
        critical: bool = False
    ):
        """Зарегистрировать задачу для выполнения при завершении"""
        task = ShutdownTask(
            name=name,
            func=func,
            priority=priority,
            timeout=timeout,
            critical=critical
        )
        
        self.shutdown_tasks.append(task)
        
        # Сортируем по приоритету (0 = высший)
        self.shutdown_tasks.sort(key=lambda t: t.priority)
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Registered shutdown task: {name}",
            category='system',
            extra_data={
                'priority': priority,
                'timeout': timeout,
                'critical': critical
            }
        )
    
    def register_before_shutdown_callback(self, callback: Callable):
        """Зарегистрировать коллбэк, вызываемый перед началом завершения"""
        self.before_shutdown_callbacks.append(callback)
    
    def register_after_shutdown_callback(self, callback: Callable):
        """Зарегистрировать коллбэк, вызываемый после завершения"""
        self.after_shutdown_callbacks.append(callback)
    
    def setup_signal_handlers(self):
        """Настроить обработчики сигналов"""
        def signal_handler(signum, frame):
            if signum == signal.SIGINT:
                reason = ShutdownReason.SIGNAL_INTERRUPT
            elif signum == signal.SIGTERM:
                reason = ShutdownReason.SIGNAL_TERMINATE
            else:
                reason = ShutdownReason.SYSTEM_SHUTDOWN
            
            asyncio.create_task(self.initiate_shutdown(reason))
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        structured_logger.log_structured(
            level='INFO',
            message="Signal handlers registered",
            category='system'
        )
    
    async def initiate_shutdown(
        self, 
        reason: ShutdownReason = ShutdownReason.USER_REQUEST,
        timeout: Optional[float] = None
    ):
        """Инициировать завершение работы"""
        if self.is_shutting_down:
            structured_logger.log_structured(
                level='WARNING',
                message="Shutdown already in progress",
                category='system',
                extra_data={'reason': reason.value}
            )
            return
        
        self.is_shutting_down = True
        self.shutdown_reason = reason
        self.shutdown_start_time = datetime.now()
        
        if timeout:
            self.shutdown_timeout = timeout
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Initiating shutdown: {reason.value}",
            category='system',
            severity='medium',
            extra_data={
                'reason': reason.value,
                'timeout': self.shutdown_timeout,
                'tasks_count': len(self.shutdown_tasks)
            }
        )
        
        # Вызываем коллбэки перед завершением
        await self._call_before_shutdown_callbacks()
        
        # Устанавливаем событие завершения
        self.shutdown_event.set()
        
        # Запускаем задачи завершения
        await self._execute_shutdown_tasks()
        
        # Вызываем коллбэки после завершения
        await self._call_after_shutdown_callbacks()
        
        # Устанавливаем событие завершения всех задач
        self.completion_event.set()
        
        structured_logger.log_structured(
            level='INFO',
            message="Shutdown completed",
            category='system',
            extra_data={
                'reason': reason.value,
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'skipped_tasks': self.skipped_tasks,
                'duration': (datetime.now() - self.shutdown_start_time).total_seconds()
            }
        )
    
    async def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """Ожидать завершения работы"""
        timeout = timeout or self.shutdown_timeout
        
        try:
            await asyncio.wait_for(self.completion_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            structured_logger.log_structured(
                level='WARNING',
                message="Shutdown timeout exceeded",
                category='system',
                severity='high',
                extra_data={'timeout': timeout}
            )
            return False
    
    def is_shutdown_requested(self) -> bool:
        """Проверить, запрошено ли завершение работы"""
        return self.shutdown_event.is_set()
    
    async def wait_for_shutdown_request(self):
        """Ожидать запроса на завершение работы"""
        await self.shutdown_event.wait()
    
    def create_cancellation_aware_task(
        self, 
        coro, 
        name: Optional[str] = None
    ) -> asyncio.Task:
        """Создать задачу, осведомленную об отмене"""
        async def cancellation_aware_wrapper():
            try:
                await coro
            except asyncio.CancelledError:
                structured_logger.log_structured(
                    level='INFO',
                    message=f"Task cancelled: {name or 'unnamed'}",
                    category='system'
                )
                raise
            except Exception as e:
                structured_logger.log_structured(
                    level='ERROR',
                    message=f"Task error: {name or 'unnamed'}: {str(e)}",
                    category='system',
                    exception=e
                )
                raise
            finally:
                self.running_tasks.discard(asyncio.current_task())
        
        task = asyncio.create_task(cancellation_aware_wrapper(), name=name)
        self.running_tasks.discard(task)  # Remove if already exists
        self.running_tasks.add(task)
        
        return task
    
    async def cancel_all_running_tasks(self):
        """Отменить все выполняющиеся задачи"""
        if not self.running_tasks:
            return
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Cancelling {len(self.running_tasks)} running tasks",
            category='system'
        )
        
        # Отменяем все задачи
        for task in self.running_tasks:
            task.cancel()
        
        # Ожидаем завершения с таймаутом
        if self.running_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.running_tasks, return_exceptions=True),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                structured_logger.log_structured(
                    level='WARNING',
                    message="Some tasks didn't finish in time",
                    category='system',
                    severity='medium'
                )
        
        self.running_tasks.clear()
    
    async def _execute_shutdown_tasks(self):
        """Выполнить задачи завершения"""
        if not self.shutdown_tasks:
            structured_logger.log_structured(
                level='INFO',
                message="No shutdown tasks registered",
                category='system'
            )
            return
        
        structured_logger.log_structured(
            level='INFO',
            message=f"Executing {len(self.shutdown_tasks)} shutdown tasks",
            category='system'
        )
        
        for task in self.shutdown_tasks:
            try:
                structured_logger.log_structured(
                    level='INFO',
                    message=f"Executing shutdown task: {task.name}",
                    category='system',
                    extra_data={
                        'priority': task.priority,
                        'timeout': task.timeout,
                        'critical': task.critical
                    }
                )
                
                # Выполняем задачу с таймаутом
                await asyncio.wait_for(task.func(), timeout=task.timeout)
                
                self.completed_tasks += 1
                
                structured_logger.log_structured(
                    level='INFO',
                    message=f"Shutdown task completed: {task.name}",
                    category='system'
                )
                
            except asyncio.TimeoutError:
                self.failed_tasks += 1
                
                structured_logger.log_structured(
                    level='ERROR',
                    message=f"Shutdown task timeout: {task.name}",
                    category='system',
                    severity='high',
                    extra_data={'timeout': task.timeout}
                )
                
                if task.critical:
                    structured_logger.log_structured(
                        level='CRITICAL',
                        message=f"Critical shutdown task failed: {task.name}",
                        category='system',
                        severity='critical'
                    )
                    # Для критических задач прерываем завершение
                    raise
                
            except Exception as e:
                self.failed_tasks += 1
                
                structured_logger.log_structured(
                    level='ERROR',
                    message=f"Shutdown task error: {task.name}: {str(e)}",
                    category='system',
                    severity='high',
                    exception=e
                )
                
                if task.critical:
                    structured_logger.log_structured(
                        level='CRITICAL',
                        message=f"Critical shutdown task failed: {task.name}",
                        category='system',
                        severity='critical'
                    )
                    # Для критических задач прерываем завершение
                    raise
            
            except asyncio.CancelledError:
                self.skipped_tasks += 1
                
                structured_logger.log_structured(
                    level='WARNING',
                    message=f"Shutdown task cancelled: {task.name}",
                    category='system'
                )
                
                if task.critical:
                    structured_logger.log_structured(
                        level='CRITICAL',
                        message=f"Critical shutdown task cancelled: {task.name}",
                        category='system',
                        severity='critical'
                    )
                    raise
    
    async def _call_before_shutdown_callbacks(self):
        """Вызвать коллбэки перед завершением"""
        for callback in self.before_shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                structured_logger.log_structured(
                    level='ERROR',
                    message=f"Before shutdown callback error: {str(e)}",
                    category='system',
                    exception=e
                )
    
    async def _call_after_shutdown_callbacks(self):
        """Вызвать коллбэки после завершения"""
        for callback in self.after_shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                structured_logger.log_structured(
                    level='ERROR',
                    message=f"After shutdown callback error: {str(e)}",
                    category='system',
                    exception=e
                )
    
    def get_shutdown_status(self) -> Dict[str, Any]:
        """Получить статус завершения"""
        duration = None
        if self.shutdown_start_time:
            duration = (datetime.now() - self.shutdown_start_time).total_seconds()
        
        return {
            'is_shutting_down': self.is_shutting_down,
            'shutdown_reason': self.shutdown_reason.value if self.shutdown_reason else None,
            'shutdown_start_time': self.shutdown_start_time.isoformat() if self.shutdown_start_time else None,
            'shutdown_duration': duration,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'skipped_tasks': self.skipped_tasks,
            'total_tasks': len(self.shutdown_tasks),
            'running_tasks': len(self.running_tasks),
            'shutdown_requested': self.is_shutdown_requested()
        }


# Глобальный экземпляр менеджера завершения
shutdown_manager = ShutdownManager()