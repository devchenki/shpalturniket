<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePingStore } from '@/stores/pingStore'

const router = useRouter()
const pingStore = usePingStore()

const loading = computed(() => pingStore.pingLoading)

const actions = [
  {
    title: 'Пинг всех устройств',
    subtitle: 'Проверить все устройства',
    icon: 'tabler-activity',
    color: 'primary',
    action: 'pingAll',
  },
  {
    title: 'Добавить устройство',
    subtitle: 'Новое устройство для мониторинга',
    icon: 'tabler-plus',
    color: 'success',
    action: 'addDevice',
  },
  {
    title: 'Обновить данные',
    subtitle: 'Перезагрузить устройства',
    icon: 'tabler-refresh',
    color: 'info',
    action: 'refreshData',
  },
  {
    title: 'Настройки уведомлений',
    subtitle: 'Telegram и email',
    icon: 'tabler-bell',
    color: 'warning',
    action: 'notifications',
  },
]

const executeAction = async (actionType: string) => {
  try {
    switch (actionType) {
      case 'pingAll':
        await pingStore.pingAllDevices()
        break
      
      case 'addDevice':
        await router.push('/ping-devices?action=add')
        break
      
      case 'refreshData':
        await pingStore.loadDevices()
        break
      
      case 'notifications':
        await router.push('/ping-settings?tab=notifications')
        break
    }
  } catch (error) {
    console.error('Ошибка выполнения действия:', error)
  }
}
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon
          icon="tabler-zap"
          size="24"
        />
        Быстрые действия
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <VList class="card-list">
        <VListItem
          v-for="action in actions"
          :key="action.action"
          :disabled="loading"
          class="px-0"
          @click="executeAction(action.action)"
        >
          <template #prepend>
            <VAvatar
              :color="action.color"
              variant="tonal"
              size="40"
            >
              <VIcon
                :icon="action.icon"
                size="20"
              />
            </VAvatar>
          </template>

          <VListItemTitle class="font-weight-medium">
            {{ action.title }}
          </VListItemTitle>
          <VListItemSubtitle>
            {{ action.subtitle }}
          </VListItemSubtitle>

          <template #append>
            <VIcon
              icon="tabler-chevron-right"
              size="20"
              class="text-medium-emphasis"
            />
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

.v-list-item {
  border-radius: 8px;
  transition: background-color 0.2s;
}

.v-list-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.04);
}
</style>
