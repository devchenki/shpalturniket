/**
 * Конфигурация приложения
 * Интеграция с существующим функционалом из fluent_gui.py и advanced_bot.py
 */

export const appConfig = {
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8771',
  apiTimeout: Number(import.meta.env.VITE_API_TIMEOUT) || 10000,

  // Application Information
  appTitle: import.meta.env.VITE_APP_TITLE || 'EXPO - Ping Monitoring System',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',

  // Features
  enableSSE: import.meta.env.VITE_ENABLE_SSE !== 'false',
  enableTelegram: import.meta.env.VITE_ENABLE_TELEGRAM !== 'false',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS !== 'false',

  // Development
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
  debug: import.meta.env.VITE_DEBUG === 'true',
  logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',

  // Ping Configuration (из fluent_gui.py)
  defaultPingInterval: 60, // seconds
  defaultTimeout: 5, // seconds
  maxRetries: 3,

  // Categories mapping (из advanced_bot.py)
  deviceCategories: {
    'C': { name: 'Центральный C', icon: '🏢' },
    'D': { name: 'Проход D', icon: '🚶' },
    'E': { name: 'Эскалатор E', icon: '🚇' },
    'F': { name: 'Переход F', icon: '🔄' },
    'G': { name: 'Вход G', icon: '🚪' },
    'H': { name: 'Зал H', icon: '🏛️' },
    'server': { name: 'Сервер', icon: '🖥️' },
    'network': { name: 'Сеть', icon: '🌐' },
    'printer': { name: 'Принтер', icon: '🖨️' },
    'other': { name: 'Прочее', icon: '📦' },
  },

  // Status colors (интеграция с Vuetify)
  statusColors: {
    online: 'success',
    offline: 'error',
    warning: 'warning',
    unknown: 'secondary',
  },

  // Notification settings
  notifications: {
    duration: 5000, // ms
    position: 'top-right',
  },

  // Chart configuration for analytics
  charts: {
    refreshInterval: 30000, // 30 seconds
    maxDataPoints: 100,
    animationDuration: 750,
  },
}

export default appConfig
