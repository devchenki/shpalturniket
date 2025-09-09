<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  stats: {
    totalDevices: number
    onlineDevices: number
    offlineDevices: number
    availabilityPercentage: number
    averageResponseTime: number
    lastUpdate: string
  }
  loading: boolean
}

const props = defineProps<Props>()

const metrics = computed(() => [
  {
    title: 'Средний отклик',
    value: props.stats.averageResponseTime > 0 ? `${props.stats.averageResponseTime}ms` : '—',
    change: props.stats.averageResponseTime > 0 ? 'Активно' : 'Нет данных',
    color: props.stats.averageResponseTime > 0 ? 'success' : 'secondary',
    icon: 'tabler-clock',
  },
  {
    title: 'Доступность',
    value: `${props.stats.availabilityPercentage}%`,
    change: props.stats.availabilityPercentage > 95 ? 'Отлично' : 'Требует внимания',
    color: props.stats.availabilityPercentage > 95 ? 'success' : 'warning',
    icon: 'tabler-activity',
  },
  {
    title: 'Офлайн устройств',
    value: props.stats.offlineDevices.toString(),
    change: props.stats.offlineDevices === 0 ? 'Все онлайн' : 'Требует проверки',
    color: props.stats.offlineDevices === 0 ? 'success' : 'error',
    icon: 'tabler-alert-triangle',
  },
  {
    title: 'Всего устройств',
    value: props.stats.totalDevices.toString(),
    change: 'В системе',
    color: 'primary',
    icon: 'tabler-devices',
  },
])
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>Ключевые метрики</VCardTitle>
    </VCardItem>

    <VCardText>
      <VList class="card-list">
        <VListItem
          v-for="metric in metrics"
          :key="metric.title"
          class="px-0"
        >
          <template #prepend>
            <VAvatar
              :color="metric.color"
              variant="tonal"
              size="40"
            >
              <VIcon
                :icon="metric.icon"
                size="20"
              />
            </VAvatar>
          </template>

          <VListItemTitle class="font-weight-medium">
            {{ metric.value }}
          </VListItemTitle>
          <VListItemSubtitle>
            {{ metric.title }}
          </VListItemSubtitle>

          <template #append>
            <VChip
              :color="metric.change.includes('+') ? 'success' : 'error'"
              size="small"
              variant="tonal"
            >
              {{ metric.change }}
            </VChip>
          </template>
        </VListItem>
      </VList>
    </VCardText>
  </VCard>
</template>

<style scoped>
.card-list {
  --v-list-gap: 16px;
}
</style>
