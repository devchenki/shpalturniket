<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'
import PingEventsCategories from './PingEventsCategories.vue'
import PingEventsDevices from './PingEventsDevices.vue'

const pingStore = usePingStore()
const notifications = useNotifications()

const activeTab = ref('categories')
const loading = ref(false)

// Инициализация
onMounted(async () => {
  loading.value = true
  try {
    await pingStore.loadEventCategories()
    await pingStore.loadAvailableDevices()
  } catch (error) {
    notifications.error('Ошибка загрузки', 'Не удалось загрузить данные мероприятий')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <VRow>
      <VCol cols="12">
        <VCard>
          <VTabs
            v-model="activeTab"
            color="primary"
            align-tabs="start"
          >
            <VTab value="categories">
              <VIcon
                icon="tabler-calendar-event"
                class="me-2"
              />
              Категории мероприятий
            </VTab>
            
            <VTab value="devices">
              <VIcon
                icon="tabler-devices"
                class="me-2"
              />
              Устройства для мероприятий
            </VTab>
          </VTabs>

          <VTabsWindow v-model="activeTab">
            <VTabsWindowItem value="categories">
              <PingEventsCategories />
            </VTabsWindowItem>
            
            <VTabsWindowItem value="devices">
              <PingEventsDevices />
            </VTabsWindowItem>
          </VTabsWindow>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>
