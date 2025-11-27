<template>
  <v-snackbar
    v-for="notification in notifications"
    :key="notification.id"
    v-model="notification.visible"
    :color="getColor(notification.type)"
    :timeout="notification.duration"
    location="top right"
    :multi-line="notification.message.length > 50"
    class="notification-snackbar"
    @update:model-value="(val) => !val && removeNotification(notification.id)"
  >
    <div class="d-flex align-center">
      <v-icon :icon="getIcon(notification.type)" class="mr-2" />
      <div class="flex-grow-1">
        <div class="text-subtitle-2 font-weight-bold">{{ notification.title }}</div>
        <div v-if="notification.message" class="text-caption">{{ notification.message }}</div>
      </div>
    </div>

    <template #actions>
      <v-btn
        icon="mdi-close"
        size="small"
        variant="text"
        @click="removeNotification(notification.id)"
      />
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useNotifications, type Notification } from '@/composables/useNotifications'

const { notifications: rawNotifications } = useNotifications()

// Добавляем поле visible для управления snackbar
interface ExtendedNotification extends Notification {
  visible: boolean
}

const notifications = ref<ExtendedNotification[]>([])

// Следим за изменениями в notifications
watch(
  () => rawNotifications,
  (newNotifications) => {
    // Добавляем новые уведомления с visible: true
    newNotifications.forEach(notif => {
      if (!notifications.value.find(n => n.id === notif.id)) {
        notifications.value.push({
          ...notif,
          visible: true,
        })
      }
    })
    
    // Удаляем старые уведомления
    notifications.value = notifications.value.filter(notif =>
      newNotifications.find(n => n.id === notif.id)
    )
  },
  { deep: true, immediate: true }
)

function removeNotification(id: string) {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.visible = false
    // Удаляем из массива после анимации
    setTimeout(() => {
      notifications.value = notifications.value.filter(n => n.id !== id)
    }, 300)
  }
}

function getColor(type: Notification['type']) {
  switch (type) {
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    default:
      return 'primary'
  }
}

function getIcon(type: Notification['type']) {
  switch (type) {
    case 'success':
      return 'mdi-check-circle'
    case 'error':
      return 'mdi-alert-circle'
    case 'warning':
      return 'mdi-alert'
    case 'info':
      return 'mdi-information'
    default:
      return 'mdi-bell'
  }
}
</script>

<style scoped>
.notification-snackbar {
  margin-top: 8px;
}
</style>
