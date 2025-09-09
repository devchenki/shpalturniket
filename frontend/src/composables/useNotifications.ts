/**
 * Композабл для управления уведомлениями
 * Интеграция с системой уведомлений из fluent_gui.py
 */

import { ref } from 'vue'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  persistent?: boolean
  timestamp: Date
}

const notifications = ref<Notification[]>([])

export const useNotifications = () => {
  // Добавить уведомление с дедупликацией
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    // Проверяем, нет ли уже такого уведомления
    const existingNotification = notifications.value.find(n => 
      n.title === notification.title && 
      n.message === notification.message &&
      n.type === notification.type
    )
    
    if (existingNotification) {
      // Обновляем время существующего уведомления
      existingNotification.timestamp = new Date()
      return existingNotification.id
    }

    const id = Date.now().toString() + Math.random().toString(36).substr(2, 9)
    
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      duration: notification.duration ?? 5000,
    }

    notifications.value.push(newNotification)

    // Автоматически удаляем уведомление через указанное время
    if (!notification.persistent && newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, newNotification.duration)
    }

    return id
  }

  // Удалить уведомление
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  // Очистить все уведомления
  const clearNotifications = () => {
    notifications.value = []
  }

  // Удобные методы для разных типов уведомлений
  const success = (title: string, message?: string, options?: Partial<Notification>) => {
    return addNotification({
      type: 'success',
      title,
      message: message || '',
      ...options,
    })
  }

  const error = (title: string, message?: string, options?: Partial<Notification>) => {
    return addNotification({
      type: 'error',
      title,
      message: message || '',
      duration: 8000, // Ошибки показываем дольше
      ...options,
    })
  }

  const warning = (title: string, message?: string, options?: Partial<Notification>) => {
    return addNotification({
      type: 'warning',
      title,
      message: message || '',
      duration: 6000,
      ...options,
    })
  }

  const info = (title: string, message?: string, options?: Partial<Notification>) => {
    return addNotification({
      type: 'info',
      title,
      message: message || '',
      ...options,
    })
  }

  // Специальные уведомления для ping мониторинга
  const deviceOnline = (deviceId: string, ip: string) => {
    return success(
      '✅ Устройство восстановлено',
      `${deviceId} (${ip}) снова онлайн`,
      { duration: 5000 }
    )
  }

  const deviceOffline = (deviceId: string, ip: string) => {
    return error(
      '🔴 Устройство недоступно',
      `${deviceId} (${ip}) не отвечает на пинг`,
      { duration: 10000, persistent: true }
    )
  }

  const deviceWarning = (deviceId: string, ip: string, responseTime: number) => {
    return warning(
      '⚠️ Медленный отклик',
      `${deviceId} (${ip}) отвечает медленно: ${responseTime}ms`,
      { duration: 6000 }
    )
  }

  const telegramBotStarted = () => {
    return success(
      'Telegram бот запущен',
      'Система уведомлений активирована',
      { duration: 3000 }
    )
  }

  const telegramBotStopped = () => {
    return info(
      'Telegram бот остановлен',
      'Система уведомлений отключена',
      { duration: 3000 }
    )
  }

  const pingAllStarted = () => {
    return info(
      '🔄 Пинг всех устройств',
      'Проверка статуса запущена...',
      { duration: 2000 }
    )
  }

  const pingAllCompleted = (stats: { total: number, online: number, offline: number }) => {
    const { total, online, offline } = stats
    return success(
      '✅ Проверка завершена',
      `Всего: ${total}, Онлайн: ${online}, Офлайн: ${offline}`,
      { duration: 4000 }
    )
  }

  return {
    // Состояние
    notifications: notifications.value,

    // Основные методы
    addNotification,
    removeNotification,
    clearNotifications,

    // Типизированные методы
    success,
    error,
    warning,
    info,

    // Специализированные методы
    deviceOnline,
    deviceOffline,
    deviceWarning,
    telegramBotStarted,
    telegramBotStopped,
    pingAllStarted,
    pingAllCompleted,
  }
}
