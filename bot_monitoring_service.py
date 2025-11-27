#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Monitoring Service for TurboShpalych Pro Bot
Авторские права (c) 2025 Shpalych Technologies. Все права защищены.

Модуль для операций мониторинга устройств с кэшированием и оптимизацией.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Перечисление статусов устройств"""
    ONLINE = "онлайн"
    OFFLINE = "офлайн"
    CHECKING = "проверка"
    UNKNOWN = "неизвестно"


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
    consecutive_failures: int = 0  # Количество последовательных неудачных проверок


@dataclass
class CategoryInfo:
    """Модель информации о категории"""
    id: str
    name: str
    icon: str
    devices: List[str] = field(default_factory=list)


@dataclass
class MonitoringStats:
    """Модель статистики мониторинга"""
    total: int
    online: int
    offline: int
    percentage: float
    last_update: datetime
    average_response_time: Optional[float] = None
    check_duration: Optional[float] = None


@dataclass
class CacheEntry:
    """Запись в кэше"""
    data: Any
    timestamp: datetime
    ttl: float


class DeviceCache:
    """Умный кэш для данных устройств"""
    
    def __init__(self, default_ttl: float = 30.0):
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Получить данные из кэша"""
        if key not in self.cache:
            self.stats['misses'] += 1
            return None
        
        entry = self.cache[key]
        
        # Проверяем TTL
        if datetime.now() - entry.timestamp > timedelta(seconds=entry.ttl):
            del self.cache[key]
            self.stats['evictions'] += 1
            self.stats['misses'] += 1
            return None
        
        self.stats['hits'] += 1
        return entry.data
    
    def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """Сохранить данные в кэше"""
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl=ttl or self.default_ttl
        )
        self.cache[key] = entry
    
    def invalidate(self, key: str) -> None:
        """Инвалидировать запись в кэше"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self) -> None:
        """Очистить кэш"""
        self.cache.clear()
        self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
    
    def cleanup_expired(self) -> int:
        """Очистить истекшие записи"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if now - entry.timestamp > timedelta(seconds=entry.ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            self.stats['evictions'] += 1
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_entries': len(self.cache),
            'hit_rate': hit_rate
        }


class RateLimiter:
    """Лимитер частоты запросов"""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
    
    async def acquire(self) -> bool:
        """Получить разрешение на выполнение запроса"""
        now = datetime.now()
        
        # Удаляем старые запросы
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(seconds=self.time_window)]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    async def wait_if_needed(self) -> None:
        """Подождать, если необходимо"""
        while not await self.acquire():
            await asyncio.sleep(0.1)


class MonitoringService:
    """Сервис для операций мониторинга устройств"""
    
    def __init__(self, ping_instance, cache_ttl: float = 30.0):
        self.ping = ping_instance
        self.cache = DeviceCache(cache_ttl)
        
        # Лимитер для частых запросов
        self.device_rate_limiter = RateLimiter(max_requests=5, time_window=1.0)
        self.batch_rate_limiter = RateLimiter(max_requests=1, time_window=2.0)
        
        # Статистика
        self.check_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0
        
        # Настройки
        self.max_concurrent_checks = 20
        self.ping_timeout = 2.0
        self.max_retries = 2
        
    async def check_device(
        self, 
        device: DeviceInfo, 
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> DeviceInfo:
        """Проверить статус одного устройства с кэшированием и оптимизацией"""
        cache_key = f"device_{device.id}"
        
        # Проверяем кэш
        if use_cache and not force_refresh:
            cached_device = self.cache.get(cache_key)
            if cached_device:
                logger.debug(f"Cache hit for device {device.id}")
                return cached_device
        
        # Лимитируем частоту запросов
        await self.device_rate_limiter.wait_if_needed()
        
        start_time = time.perf_counter()
        
        try:
            device.status = DeviceStatus.CHECKING.value
            device.last_check = datetime.now()
            
            # Выполняем пинг с повторными попытками
            is_online = await self._ping_with_retry(device.ip)
            
            check_duration = time.perf_counter() - start_time
            
            if is_online:
                device.status = DeviceStatus.ONLINE.value
                device.consecutive_failures = 0
                
                # Замеряем время отклика
                device.response_time = await self._measure_response_time(device.ip)
            else:
                device.status = DeviceStatus.OFFLINE.value
                device.consecutive_failures += 1
                device.response_time = None
            
            # Обновляем статистику
            self.check_count += 1
            self.total_response_time += check_duration
            
            if not is_online:
                self.failure_count += 1
            
            logger.info(f"Device {device.id} checked: {device.status} in {check_duration:.3f}s")
            
        except Exception as e:
            logger.error(f"Error checking device {device.id}: {e}")
            device.status = DeviceStatus.UNKNOWN.value
            device.consecutive_failures += 1
            device.response_time = None
            device.last_check = datetime.now()
            
            self.failure_count += 1
        
        # Сохраняем в кэш
        cache_ttl = 60.0 if device.status == DeviceStatus.ONLINE.value else 30.0
        self.cache.set(cache_key, DeviceInfo(**device.__dict__), ttl=cache_ttl)
        
        return device
    
    async def check_multiple_devices(
        self, 
        devices: List[DeviceInfo], 
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> List[DeviceInfo]:
        """Проверить несколько устройств одновременно с контролем параллелизма"""
        if not devices:
            return []
        
        start_time = time.perf_counter()
        
        # Лимитируем частоту пакетных запросов
        await self.batch_rate_limiter.wait_if_needed()
        
        # Разделяем устройства на группы для контроля параллелизма
        results = []
        
        for i in range(0, len(devices), self.max_concurrent_checks):
            batch = devices[i:i + self.max_concurrent_checks]
            
            # Создаем задачи для текущей партии
            tasks = [
                self.check_device(device, use_cache, force_refresh) 
                for device in batch
            ]
            
            # Выполняем параллельно
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in batch check for device {batch[j].id}: {result}")
                    # Создаем устройство со статусом ошибки
                    error_device = DeviceInfo(
                        id=batch[j].id,
                        ip=batch[j].ip,
                        location=batch[j].location,
                        category=batch[j].category,
                        status=DeviceStatus.UNKNOWN.value,
                        last_check=datetime.now(),
                        response_time=None
                    )
                    results.append(error_device)
                else:
                    results.append(result)
        
        check_duration = time.perf_counter() - start_time
        logger.info(f"Checked {len(devices)} devices in {check_duration:.3f}s")
        
        return results
    
    async def get_device_status(self, device_id: str) -> Optional[DeviceInfo]:
        """Получить статус устройства из кэша"""
        cache_key = f"device_{device_id}"
        return self.cache.get(cache_key)
    
    def get_statistics(self, devices: List[DeviceInfo]) -> MonitoringStats:
        """Рассчитать детальную статистику мониторинга"""
        total = len(devices)
        online = sum(1 for d in devices if d.status == DeviceStatus.ONLINE.value)
        offline = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE.value)
        unknown = sum(1 for d in devices if d.status == DeviceStatus.UNKNOWN.value)
        
        percentage = (online / total * 100) if total > 0 else 0
        
        # Рассчитываем среднее время отклика
        response_times = [d.response_time for d in devices if d.response_time is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return MonitoringStats(
            total=total,
            online=online,
            offline=offline,
            percentage=percentage,
            last_update=datetime.now(),
            average_response_time=avg_response_time
        )
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Получить статистику сервиса мониторинга"""
        cache_stats = self.cache.get_stats()
        
        avg_response_time = (self.total_response_time / self.check_count 
                           if self.check_count > 0 else 0)
        
        failure_rate = (self.failure_count / self.check_count * 100 
                       if self.check_count > 0 else 0)
        
        return {
            'checks_performed': self.check_count,
            'failures': self.failure_count,
            'failure_rate': failure_rate,
            'average_response_time': avg_response_time,
            'cache': cache_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        try:
            # Проверяем доступность ping модуля
            test_result = await asyncio.to_thread(self.ping.ping_ip, "8.8.8.8")
            
            # Очищаем истекшие записи кэша
            expired_count = self.cache.cleanup_expired()
            
            return {
                'status': 'healthy',
                'ping_available': test_result is not None,
                'cache_entries': len(self.cache.cache),
                'expired_cleaned': expired_count,
                'service_stats': self.get_service_stats()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def reset_statistics(self) -> None:
        """Сбросить статистику"""
        self.check_count = 0
        self.failure_count = 0
        self.total_response_time = 0.0
        self.cache.clear()
    
    async def _ping_with_retry(self, ip: str) -> bool:
        """Выполнить пинг с повторными попытками"""
        for attempt in range(self.max_retries + 1):
            try:
                result = await asyncio.to_thread(self.ping.ping_ip, ip)
                if result is not None:
                    return result
            except Exception as e:
                logger.debug(f"Ping attempt {attempt + 1} failed for {ip}: {e}")
            
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (attempt + 1))  # Экспоненциальная задержка
        
        return False
    
    async def _measure_response_time(self, ip: str) -> Optional[float]:
        """Измерить время отклика"""
        try:
            start_time = time.perf_counter()
            result = await asyncio.to_thread(self.ping.ping_ip, ip)
            end_time = time.perf_counter()
            
            if result is not None:
                return (end_time - start_time) * 1000.0  # в миллисекундах
            
        except Exception as e:
            logger.debug(f"Response time measurement failed for {ip}: {e}")
        
        return None