<script setup lang="ts">
import PingAnalyticsCharts from '@/views/ping/analytics/PingAnalyticsCharts.vue'
import PingAnalyticsMetrics from '@/views/ping/analytics/PingAnalyticsMetrics.vue'
import PingAnalyticsEvents from '@/views/ping/analytics/PingAnalyticsEvents.vue'

definePage({
  meta: {
    title: 'Аналитика - Ping мониторинг',
  },
})
</script>

<template>
  <VRow class="match-height">
    <!-- 👉 Метрики -->
    <VCol
      cols="12"
      md="4"
    >
      <PingAnalyticsMetrics />
    </VCol>

    <!-- 👉 Графики -->
    <VCol
      cols="12"
      md="8"
    >
      <PingAnalyticsCharts />
    </VCol>

    <!-- 👉 История событий -->
    <VCol cols="12">
      <PingAnalyticsEvents />
    </VCol>
  </VRow>
</template>
