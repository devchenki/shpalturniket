<template>
  <div class="ping-analytics">
    <!-- Заголовок страницы -->
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold mb-2">
          📊 Аналитика системы
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Детальная аналитика работы системы мониторинга турникетов
        </p>
      </div>
      
      <VBtn
        color="primary"
        prepend-icon="tabler-refresh"
        @click="refreshData"
        :loading="loading"
      >
        Обновить данные
      </VBtn>
    </div>

    <!-- Метрики -->
    <PingAnalyticsMetrics 
      :stats="analyticsStats"
      :loading="loading"
    />

    <!-- Графики -->
    <PingAnalyticsCharts 
      :data="chartData"
      :loading="loading"
    />

    <!-- События -->
    <PingAnalyticsEvents 
      :events="recentEvents"
      :loading="loading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'
import PingAnalyticsMetrics from './PingAnalyticsMetrics.vue'
import PingAnalyticsCharts from './PingAnalyticsCharts.vue'
import PingAnalyticsEvents from './PingAnalyticsEvents.vue'

const pingStore = usePingStore()
const notifications = useNotifications()

// Состояние
const loading = ref(false)

// Вычисляемые свойства
const analyticsStats = computed(() => {
  const devices = pingStore.devices
  const total = devices.length
  const online = devices.filter(d => d.status === 'online').length
  const offline = devices.filter(d => d.status === 'offline').length
  const availability = total > 0 ? (online / total * 100) : 0

  return {
    totalDevices: total,
    onlineDevices: online,
    offlineDevices: offline,
    availabilityPercentage: Math.round(availability * 10) / 10,
    averageResponseTime: calculateAverageResponseTime(devices),
    lastUpdate: new Date().toLocaleString('ru-RU')
  }
})

const chartData = computed(() => {
  // Данные для графиков на основе реальных данных
  const devices = pingStore.devices
  const now = new Date()
  
  // Генерируем данные за последние 24 часа
  const hours = Array.from({ length: 24 }, (_, i) => {
    const hour = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000)
    return hour.getHours()
  })

  const availabilityData = hours.map(hour => {
    // Симуляция данных доступности (в реальности брать из истории)
    const baseAvailability = analyticsStats.value.availabilityPercentage
    const variation = (Math.random() - 0.5) * 10
    return Math.max(0, Math.min(100, baseAvailability + variation))
  })

  const responseTimeData = hours.map(() => {
    // Симуляция данных времени отклика
    const baseTime = analyticsStats.value.averageResponseTime
    const variation = (Math.random() - 0.5) * 20
    return Math.max(0, baseTime + variation)
  })

  return {
    availability: {
      labels: hours.map(h => `${h}:00`),
      data: availabilityData
    },
    responseTime: {
      labels: hours.map(h => `${h}:00`),
      data: responseTimeData
    }
  }
})

const recentEvents = computed(() => {
  return pingStore.recentEvents.slice(0, 10)
})

// Методы
const calculateAverageResponseTime = (devices: any[]) => {
  const devicesWithResponseTime = devices.filter(d => d.response_ms && d.response_ms > 0)
  if (devicesWithResponseTime.length === 0) return 0
  
  const total = devicesWithResponseTime.reduce((sum, d) => sum + d.response_ms, 0)
  return Math.round(total / devicesWithResponseTime.length)
}

const refreshData = async () => {
  loading.value = true
  try {
    await Promise.all([
      pingStore.loadDevices(),
      pingStore.loadFullConfig()
    ])
    notifications.success('Данные аналитики обновлены')
  } catch (error) {
    notifications.error('Ошибка обновления данных аналитики')
    console.error('Ошибка обновления аналитики:', error)
  } finally {
    loading.value = false
  }
}

// Инициализация
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.ping-analytics {
  padding: 24px;
}

@media (max-width: 768px) {
  .ping-analytics {
    padding: 16px;
  }
}
</style>
