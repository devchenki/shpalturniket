<script setup lang="ts">
import { computed } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import NotificationItem from './NotificationItem.vue'

const { notifications, removeNotification } = useNotifications()

const sortedNotifications = computed(() => {
  return [...notifications].sort((a, b) => 
    b.timestamp.getTime() - a.timestamp.getTime()
  )
})
</script>

<template>
  <VSlideYTransition group>
    <div
      v-for="notification in sortedNotifications"
      :key="notification.id"
      class="notification-wrapper"
    >
      <NotificationItem
        :notification="notification"
        @close="removeNotification"
      />
    </div>
  </VSlideYTransition>
</template>

<style scoped>
.notification-wrapper {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 400px;
  width: 100%;
}

.notification-wrapper + .notification-wrapper {
  margin-top: 8px;
}

@media (max-width: 600px) {
  .notification-wrapper {
    right: 16px;
    left: 16px;
    max-width: none;
  }
}
</style>
