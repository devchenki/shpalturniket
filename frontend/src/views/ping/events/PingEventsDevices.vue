<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'
import type { EventDeviceUpdate } from '@/api/pingApi'

const pingStore = usePingStore()
const notifications = useNotifications()

const loading = ref(false)
const selectedCategoryId = ref<number | null>(null)
const deviceSelections = ref<Map<string, boolean>>(new Map())

// Вычисляемые свойства
const selectedCategory = computed(() => {
  if (!selectedCategoryId.value) return null
  return pingStore.eventCategories.find(cat => cat.id === selectedCategoryId.value)
})

const availableDevices = computed(() => {
  return pingStore.availableDevices || []
})

const selectedDevices = computed(() => {
  const selected: EventDeviceUpdate[] = []
  deviceSelections.value.forEach((isEnabled, deviceId) => {
    selected.push({
      device_id: deviceId,
      is_enabled: isEnabled
    })
  })
  return selected
})

// Выбрать категорию
const selectCategory = (categoryId: number) => {
  selectedCategoryId.value = categoryId
  loadCategoryDevices()
}

// Загрузить устройства категории
const loadCategoryDevices = async () => {
  if (!selectedCategoryId.value) return
  
  loading.value = true
  try {
    const devices = await pingStore.getCategoryDevices(selectedCategoryId.value)
    
    // Инициализируем выбор устройств
    deviceSelections.value.clear()
    availableDevices.value.forEach(device => {
      const isSelected = devices.some(ed => ed.device_id === device.device_id && ed.is_enabled)
      deviceSelections.value.set(device.device_id, isSelected)
    })
  } catch (error) {
    notifications.error('Ошибка загрузки', 'Не удалось загрузить устройства категории')
  } finally {
    loading.value = false
  }
}

// Переключить устройство
const toggleDevice = (deviceId: string) => {
  const currentValue = deviceSelections.value.get(deviceId) || false
  deviceSelections.value.set(deviceId, !currentValue)
}

// Сохранить выбор устройств
const saveDeviceSelection = async () => {
  if (!selectedCategoryId.value) return
  
  loading.value = true
  try {
    await pingStore.addDevicesToCategory(selectedCategoryId.value, selectedDevices.value)
    notifications.success('Устройства сохранены', 'Выбор устройств для мероприятия сохранен')
    await pingStore.loadEventCategories() // Обновляем статистику
  } catch (error) {
    notifications.error('Ошибка сохранения', 'Не удалось сохранить выбор устройств')
  } finally {
    loading.value = false
  }
}

// Инициализация
onMounted(async () => {
  await pingStore.loadEventCategories()
  await pingStore.loadAvailableDevices()
})
</script>

<template>
  <VCardText>
    <!-- Заголовок -->
    <div class="mb-6">
      <h6 class="text-h6 mb-1">
        Устройства для мероприятий
      </h6>
      <p class="text-body-2 text-medium-emphasis">
        Выберите категорию мероприятия и настройте какие устройства будут использоваться
      </p>
    </div>

    <!-- Выбор категории -->
    <VCard
      variant="outlined"
      class="mb-6"
    >
      <VCardTitle>
        Выберите категорию мероприятия
      </VCardTitle>
      
      <VCardText>
        <VRow>
          <VCol
            v-for="category in pingStore.eventCategories"
            :key="category.id"
            cols="12"
            sm="6"
            md="4"
          >
            <VCard
              :variant="selectedCategoryId === category.id ? 'elevated' : 'outlined'"
              :color="selectedCategoryId === category.id ? 'primary' : undefined"
              class="cursor-pointer"
              @click="selectCategory(category.id!)"
            >
              <VCardText class="text-center">
                <VIcon
                  icon="tabler-calendar-event"
                  size="32"
                  :color="selectedCategoryId === category.id ? 'white' : 'primary'"
                  class="mb-2"
                />
                <div
                  :class="selectedCategoryId === category.id ? 'text-white' : 'text-primary'"
                  class="font-weight-bold"
                >
                  {{ category.name }}
                </div>
                <div
                  :class="selectedCategoryId === category.id ? 'text-white' : 'text-medium-emphasis'"
                  class="text-caption"
                >
                  {{ category.enabled_devices_count }}/{{ category.total_devices_count }} устройств
                </div>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Выбор устройств -->
    <VCard
      v-if="selectedCategory"
      variant="outlined"
    >
      <VCardTitle class="d-flex align-center justify-space-between">
        <span>Устройства для "{{ selectedCategory.name }}"</span>
        <VBtn
          color="primary"
          :loading="loading"
          @click="saveDeviceSelection"
        >
          Сохранить выбор
        </VBtn>
      </VCardTitle>
      
      <VCardText>
        <VRow>
          <VCol
            v-for="device in availableDevices"
            :key="device.device_id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <VCard
              :variant="deviceSelections.get(device.device_id) ? 'elevated' : 'outlined'"
              :color="deviceSelections.get(device.device_id) ? 'success' : undefined"
              class="cursor-pointer"
              @click="toggleDevice(device.device_id)"
            >
              <VCardText>
                <div class="d-flex align-center justify-space-between mb-2">
                  <VCheckbox
                    :model-value="deviceSelections.get(device.device_id) || false"
                    :color="deviceSelections.get(device.device_id) ? 'success' : 'primary'"
                    hide-details
                    @click.stop="toggleDevice(device.device_id)"
                  />
                  
                  <VChip
                    :color="device.enabled ? 'success' : 'error'"
                    size="small"
                  >
                    {{ device.enabled ? 'Включено' : 'Отключено' }}
                  </VChip>
                </div>
                
                <div
                  :class="deviceSelections.get(device.device_id) ? 'text-white' : 'text-primary'"
                  class="font-weight-bold mb-1"
                >
                  {{ device.device_id }}
                </div>
                
                <div
                  :class="deviceSelections.get(device.device_id) ? 'text-white' : 'text-medium-emphasis'"
                  class="text-caption mb-1"
                >
                  {{ device.ip }}
                </div>
                
                <div
                  :class="deviceSelections.get(device.device_id) ? 'text-white' : 'text-medium-emphasis'"
                  class="text-caption"
                >
                  {{ device.description }}
                </div>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Пустое состояние -->
    <VCard
      v-else-if="pingStore.eventCategories.length === 0"
      variant="outlined"
      class="text-center py-8"
    >
      <VCardText>
        <VIcon
          icon="tabler-calendar-event"
          size="64"
          class="text-medium-emphasis mb-4"
        />
        <h6 class="text-h6 mb-2">
          Нет категорий мероприятий
        </h6>
        <p class="text-body-2 text-medium-emphasis">
          Сначала создайте категорию мероприятия
        </p>
      </VCardText>
    </VCard>

    <!-- Инструкция -->
    <VCard
      v-else
      variant="outlined"
      class="text-center py-4"
    >
      <VCardText>
        <VIcon
          icon="tabler-info-circle"
          size="32"
          class="text-primary mb-2"
        />
        <div class="text-body-2 text-medium-emphasis">
          Выберите категорию мероприятия выше, чтобы настроить устройства
        </div>
      </VCardText>
    </VCard>
  </VCardText>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
  transition: all 0.2s ease;
}

.cursor-pointer:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
</style>
