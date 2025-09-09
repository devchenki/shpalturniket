<script setup lang="ts">
import type { Notification } from '@/composables/useNotifications'

interface Props {
  notification: Notification
}

interface Emits {
  (e: 'close', id: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'success': return 'success'
    case 'error': return 'error'
    case 'warning': return 'warning'
    case 'info': return 'info'
    default: return 'primary'
  }
}

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'success': return 'tabler-check'
    case 'error': return 'tabler-x'
    case 'warning': return 'tabler-alert-triangle'
    case 'info': return 'tabler-info-circle'
    default: return 'tabler-bell'
  }
}
</script>

<template>
  <VAlert
    :color="getNotificationColor(notification.type)"
    :icon="getNotificationIcon(notification.type)"
    closable
    elevation="2"
    class="notification-alert"
    variant="flat"
    @click:close="emit('close', notification.id)"
  >
    <template #title>
      <span class="text-sm font-weight-medium">
        {{ notification.title }}
      </span>
    </template>
    
    <div v-if="notification.message" class="text-caption mt-1">
      {{ notification.message }}
    </div>

    <div class="text-caption opacity-60 mt-1">
      {{ notification.timestamp.toLocaleTimeString('ru-RU') }}
    </div>
  </VAlert>
</template>

<style scoped>
.notification-alert {
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 3px solid;
  backdrop-filter: blur(8px);
  max-width: 400px;
}

.notification-alert:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
  transition: all 0.2s ease;
}

/* Улучшенная читаемость текста */
.notification-alert :deep(.v-alert__content) {
  color: inherit;
}

.notification-alert :deep(.v-alert__title) {
  color: inherit;
  font-weight: 500;
}

.notification-alert :deep(.v-alert__text) {
  color: inherit;
  opacity: 0.9;
}
</style>
