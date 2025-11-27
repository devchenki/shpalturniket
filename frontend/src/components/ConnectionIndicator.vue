<template>
  <v-chip
    :color="statusColor"
    :prepend-icon="statusIcon"
    variant="flat"
    size="small"
    class="connection-indicator"
  >
    <span class="text-caption">{{ statusText }}</span>
    <v-tooltip activator="parent" location="bottom">
      <div class="text-caption">
        <div><strong>Статус:</strong> {{ statusText }}</div>
        <div v-if="lastHeartbeat">
          <strong>Последний heartbeat:</strong> {{ formatHeartbeat(lastHeartbeat) }}
        </div>
        <div v-if="status === 'reconnecting'">
          <strong>Попытка переподключения...</strong>
        </div>
      </div>
    </v-tooltip>
  </v-chip>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  status: 'connected' | 'disconnected' | 'reconnecting' | 'failed'
  lastHeartbeat?: Date | null
}

const props = defineProps<Props>()

const statusColor = computed(() => {
  switch (props.status) {
    case 'connected':
      return 'success'
    case 'reconnecting':
      return 'warning'
    case 'disconnected':
      return 'error'
    case 'failed':
      return 'error'
    default:
      return 'grey'
  }
})

const statusIcon = computed(() => {
  switch (props.status) {
    case 'connected':
      return 'mdi-check-circle'
    case 'reconnecting':
      return 'mdi-refresh'
    case 'disconnected':
      return 'mdi-alert-circle'
    case 'failed':
      return 'mdi-close-circle'
    default:
      return 'mdi-help-circle'
  }
})

const statusText = computed(() => {
  switch (props.status) {
    case 'connected':
      return 'Подключено'
    case 'reconnecting':
      return 'Переподключение...'
    case 'disconnected':
      return 'Отключено'
    case 'failed':
      return 'Ошибка'
    default:
      return 'Неизвестно'
  }
})

function formatHeartbeat(date: Date) {
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diff < 10) return 'только что'
  if (diff < 60) return `${diff} сек назад`
  
  const minutes = Math.floor(diff / 60)
  if (minutes < 60) return `${minutes} мин назад`
  
  const hours = Math.floor(minutes / 60)
  return `${hours} ч назад`
}
</script>

<style scoped>
.connection-indicator {
  cursor: default;
}
</style>
