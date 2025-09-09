<script setup lang="ts">
import PingDashboardStats from '@/views/ping/dashboard/PingDashboardStats.vue'
import PingDashboardQuickActions from '@/views/ping/dashboard/PingDashboardQuickActions.vue'
import PingDashboardRecentEvents from '@/views/ping/dashboard/PingDashboardRecentEvents.vue'
import PingDashboardTelegramStatus from '@/views/ping/dashboard/PingDashboardTelegramStatus.vue'

definePage({
  meta: {
    title: 'Панель управления - Ping мониторинг',
  },
})
</script>

<template>
  <VRow class="match-height">
    <!-- 👉 Статистика устройств -->
    <VCol
      cols="12"
      md="8"
    >
      <PingDashboardStats />
    </VCol>

    <!-- 👉 Статус Telegram -->
    <VCol
      cols="12"
      md="4"
    >
      <PingDashboardTelegramStatus />
    </VCol>

    <!-- 👉 Быстрые действия -->
    <VCol
      cols="12"
      md="6"
    >
      <PingDashboardQuickActions />
    </VCol>

    <!-- 👉 Последние события -->
    <VCol
      cols="12"
      md="6"
    >
      <PingDashboardRecentEvents />
    </VCol>
  </VRow>
</template>
